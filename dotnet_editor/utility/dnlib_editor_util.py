from __future__ import annotations

from typing import TYPE_CHECKING

from dotnet_editor.utility.utility import info_logging_with_no_line_num, error_logging_with_no_line_num

if TYPE_CHECKING:
    from dotnet_editor.eh_clause_group import EhClauseGroup
    from dotnet_editor.method_detail import MethodDetail

from dotnet_editor.dnlib_module_details import DnLibModuleDetail
from dotnet_editor.utility.dnlib_loader import load_dnlib

load_dnlib()
from dnlib.IO import DataStreamFactory, DataReader
from System import Array, Byte, UInt32, UInt16
from dnlib.DotNet.Emit import MethodBodyReader, Local


def bytes_to_data_reader(byte_data: bytes):
    byte_array = Array[Byte](byte_data)
    stream = DataStreamFactory.Create(byte_array)
    reader = DataReader(stream, UInt32(0), UInt32(len(byte_data)))
    return reader


def make_local_ivariable(local):
    return Local(local.Type)


def construct_method_from_captured(method_token, captured_method_detail: MethodDetail, eh_clause_group: EhClauseGroup, dnlib_method_detail: DnLibModuleDetail):
    method_def_md: "MethodDefMD" = dnlib_method_detail.get_method(method_token).method_def_md

    il_bytes = Array[Byte](bytes(captured_method_detail.il_codes))
    eh_bytes = Array[Byte](eh_clause_group.to_bytes())

    # verify eh count
    if captured_method_detail.eh_count != 0 and captured_method_detail.eh_count != eh_clause_group.eh_count():
        error_logging_with_no_line_num(f"EhCount mismatched > [{dnlib_method_detail.get_method(method_token).full_method_name}] [{hex(captured_method_detail.method_token)}] | CapturedMethodDetail: {captured_method_detail.eh_count} | EhClauseGroup: {eh_clause_group.eh_count()}")
        # if not qprompt.ask_yesno("Copy the log details for further analysis. Continue?",dft="y"):sys.exit()
        raise Exception(f"EhCount mistmatched.")

    # calculate the flag because it is very important
    max_stack = captured_method_detail.max_stack
    il_code_size = captured_method_detail.il_codes_size
    # eh_count = captured_method_detail.eh_count
    eh_count = eh_clause_group.eh_count() # better to take count directly
    local_var_sig_tok = method_def_md.Body.LocalVarSigTok
    if len(captured_method_detail.local_var_sig_bytes) > 0:
        try:
            local_var_sig_tok = dnlib_method_detail.get_local_var_sig_tok(captured_method_detail.local_var_sig_bytes)
        except Exception as e:
            error_logging_with_no_line_num(f"Error at: [{captured_method_detail.method_full_name}|{dnlib_method_detail.get_method(method_token).full_method_name}] [{hex(captured_method_detail.method_token)} | {hex(dnlib_method_detail.get_method(method_token).md_token)} ]")
            raise e

    info_logging_with_no_line_num(f"\t[#]local_var_sig_tok [{captured_method_detail.method_full_name}|{dnlib_method_detail.get_method(method_token).full_method_name}] [{hex(captured_method_detail.method_token)}]>> {local_var_sig_tok}")

    init_locals = method_def_md.Body.get_InitLocals()
    flags = 0b_00_00_00_00
    if init_locals == True:
        flags = flags | 0b_00_01_00_00  # 16
    if eh_count > 0:
        flags = flags | 0b_00_00_10_00  # 8

    parametres = method_def_md.Parameters
    cil_body = MethodBodyReader.CreateCilBody(dnlib_method_detail.module, il_bytes, eh_bytes, parametres, UInt16(flags), max_stack, il_code_size, local_var_sig_tok)
    return cil_body
