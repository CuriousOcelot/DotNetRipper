import os
import sys
from typing import Dict

import qprompt

from dotnet_editor.captured_methods import CapturedMethods, MethodDetail
from dotnet_editor.dnlib_module_details import DnLibModuleDetail
from dotnet_editor.utility.arg_parser_helper import ArgParserHelper
from dotnet_editor.utility.dnlib_editor_util import construct_method_from_captured, make_local_ivariable
from dotnet_editor.utility.logger_util_no_line_num import LogFormat
from dotnet_editor.utility.utility import info_logging_with_no_line_num, int_to_hex, sha256sum, sha256sum_bytes, error_logging_with_no_line_num, bytes_to_hex_list

if __name__ == '__main__':
    arg_parser_helper = ArgParserHelper.parse_args()

    flag_test_mode = arg_parser_helper.flag_test_mode
    flag_skip_qprompt = arg_parser_helper.flag_skip_qprompt
    file_path = arg_parser_helper.input_file_path
    output_file_path = arg_parser_helper.output_file_path
    windbg_output = arg_parser_helper.windebug_output
    folder_name = arg_parser_helper.folder_name

    print(f"flag_test_mode = {flag_test_mode}")
    print(f"flag_skip_qprompt = {flag_skip_qprompt}")
    print(f"file_path = {file_path}")
    print(f"output_file_path = {output_file_path}")
    print(f"windbg_output = {windbg_output}")
    print(f"folder_name = {folder_name}")

    if not flag_skip_qprompt and not qprompt.ask_yesno(f"Edit the file: {file_path}"):
        sys.exit(1)
    # load the dll module
    info_logging_with_no_line_num(f"Parsing: {file_path}")
    with open(file_path, "rb") as reader:
        dll_content = reader.read()
    dnlib_module_detail = DnLibModuleDetail(dll_content)

    # Load captured methods
    captured_methods = CapturedMethods(windbg_output, folder_name, file_path)
    captured_methods_dict: Dict[int, MethodDetail] = captured_methods.method_details
    # check if all the method parse by dnblib is caputured

    for token in dnlib_module_detail.token_to_method_map:
        arg_sinature = dnlib_module_detail.get_arg_signature(token)
        if token not in captured_methods_dict:
            error_logging_with_no_line_num(f"Not captured: {dnlib_module_detail.get_method(token).full_method_name} Token: {hex(token)}")
            raise Exception(f"Not captured method.")
        else:
            if arg_sinature != captured_methods_dict[token].arg_sig_bytes:
                error_logging_with_no_line_num(f"Argsig not same: {dnlib_module_detail.get_method(token).full_method_name} Token: {hex(token)}")
                raise Exception(f"Argsig not same.")

    # Now lets loop again to edit
    for token, method in dnlib_module_detail.token_to_method_map.items():
        method_def_md = method.method_def_md
        arg_sinature = dnlib_module_detail.get_arg_signature(token)
        captured_method_detail: MethodDetail = captured_methods_dict[token]
        eh_clause_group = captured_methods.get_eh_clause_group(token)
        constructed_cil_body = construct_method_from_captured(token, captured_method_detail, eh_clause_group, dnlib_module_detail)

        method_def_md.Body.Instructions.Clear()
        method_def_md.Body.ExceptionHandlers.Clear()
        method_def_md.Body.Variables.Clear()

        local_map = {}
        for local in constructed_cil_body.Variables:
            new_local = make_local_ivariable(local)
            method_def_md.Body.Variables.Add(new_local)
            local_map[local] = new_local

        for inst in constructed_cil_body.Instructions:
            method_def_md.Body.Instructions.Add(inst)

        for exception_handler in constructed_cil_body.ExceptionHandlers:
            method_def_md.Body.ExceptionHandlers.Add(exception_handler)

        method_def_md.Body.MaxStack = constructed_cil_body.MaxStack  # copy the captured max stack
        method_def_md.Body.KeepOldMaxStack = True  # Because we don't want to recalculate as it is set from captured data.

        info_logging_with_no_line_num("\n")
        info_logging_with_no_line_num(f"\t[*] Token: {int_to_hex(token)}", )
        info_logging_with_no_line_num(f"\t[*] Name: {method.full_method_name}", )
        info_logging_with_no_line_num(f"\t[*] info->args.pSig : {' '.join(bytes_to_hex_list(captured_method_detail.arg_sig_bytes))}")
        if len(captured_method_detail.local_var_sig_bytes) == 0:
            info_logging_with_no_line_num(f"\t[*] info->locals.pSig : Empty")
        else:
            info_logging_with_no_line_num(f"\t[*] info->locals.pSig : {' '.join(bytes_to_hex_list(captured_method_detail.local_var_sig_bytes))}")
    edited_module_bytes = dnlib_module_detail.get_module_bytes()
    if not flag_test_mode:  # Test mode will not write to output
        parent_output_path = os.path.basename(os.path.dirname(output_file_path)).strip()
        unwritable_folder = ["test_binary_x64", "test_binary_x86"]
        if parent_output_path.lower() in unwritable_folder:
            raise Exception(f"Please don't write in {', '.join(unwritable_folder)}")

        with open(output_file_path, "wb") as writer:
            writer.write(edited_module_bytes)

        info_logging_with_no_line_num(f"Wrote at: {output_file_path}", extra=LogFormat.BLUE_UNDERLINE)

    """
    Actual extraction part code end at above line
    """

    original_sha256sum = sha256sum(file_path)

    output_sha256sum = sha256sum_bytes(edited_module_bytes)

    info_logging_with_no_line_num(f"Original sha256sum: {original_sha256sum}")
    info_logging_with_no_line_num(f"Output sha256sum: {output_sha256sum}")
    info_logging_with_no_line_num(f"Filename: {file_path}")

    flag_test_successfull_code = 100
    if flag_test_mode:
        prestore_out_checksum = sha256sum(output_file_path)
        if output_sha256sum == prestore_out_checksum:
            info_logging_with_no_line_num("Successfully unpacked", extra=LogFormat.BLUE_UNDERLINE)
            flag_test_successfull_code = 200
        else:
            error_logging_with_no_line_num(
                f"Unpack failed: expected > {prestore_out_checksum} | got >{output_sha256sum}")
            flag_test_successfull_code = 404

    # if arg_parser_helper.flag_no_argument_passed:
    #     arg_parser_helper.parser.print_help()

    if flag_test_mode:
        sys.exit(flag_test_successfull_code)
