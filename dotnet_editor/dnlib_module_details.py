import logging
from typing import Dict

from dotnet_editor.dotnet_method import DotNetMethod
from dotnet_editor.utility.dnlib_loader import load_dnlib
from dotnet_editor.utility.logger_util import getlogger

load_dnlib()
from dnlib.DotNet import ModuleDefMD
from System.IO import MemoryStream

logger = getlogger(__name__.split(".")[-1], logging.DEBUG)


class DnLibModuleDetail:

    def __init__(self, data: bytes):
        stream = MemoryStream(bytearray(data))
        self._module = ModuleDefMD.Load(stream)
        self._token_to_method_map: Dict[int, DotNetMethod] = {}

        table_stream = self._module.Metadata.TablesStream
        # Argument signatures
        self._method_args_sig: Dict[int, bytes] = {}
        for rid in range(0, self._module.TablesStream.MethodTable.Rows + 2):
            method_token = (0x06 << 24) | rid
            result, raw_method_row = table_stream.TryReadMethodRow(rid)
            if not result:
                continue
            signature = raw_method_row.Signature
            data_reader = self._module.BlobStream.CreateReader(signature)
            length = data_reader.Length
            content = bytes(bytearray(data_reader.ReadBytes(length)))
            self._method_args_sig[method_token] = content

        # StandAloneSig
        stand_alone_sig_table = table_stream.StandAloneSigTable
        self._sig_to_local_var_sig_tok_map: Dict[bytes, int] = {}
        for rid in range(stand_alone_sig_table.Rows + 2):
            stand_alone_sig = self._module.ResolveStandAloneSig(rid)
            if stand_alone_sig is None:
                continue
            local_var_sig_tok = (0x11 << 24) | rid
            blob = bytes(self._module.ReadBlob(local_var_sig_tok))
            self._sig_to_local_var_sig_tok_map[blob] = local_var_sig_tok

        for type_def in self._module.GetTypes():
            for method_def_md in type_def.Methods:
                if method_def_md.IsAbstract == True:  # skip the abstract methods
                    continue
                if method_def_md.IsPinvokeImpl == True:  # skip the pinvoke methods
                    continue
                if method_def_md.HasBody == False:  # skip if it has no body
                    continue
                md_token = method_def_md.MDToken.get_Raw()
                param_types = []
                is_static_method = None
                for param in method_def_md.Parameters:
                    if param.get_IsHiddenThisParameter():
                        if is_static_method is None:
                            is_static_method = False  # because it is this parametre
                        continue
                    else:
                        if is_static_method is None:
                            is_static_method = True  # because it is this parametre
                        param_types.append(param.Type.FullName)
                if is_static_method is None:
                    is_static_method = True

                dotnet_method_detail = DotNetMethod(
                    md_token,
                    method_def_md,
                    type_def.FullName,
                    method_def_md.Name,
                    param_types,
                    is_static_method,
                )
                self._token_to_method_map[md_token] = dotnet_method_detail

        pass

    @property
    def module(self):
        return self._module

    @property
    def token_to_method_map(self) -> Dict[int, DotNetMethod]:
        return self._token_to_method_map

    def get_method(self, token) -> DotNetMethod:
        return self._token_to_method_map[token]

    def get_module_bytes(self):
        ms = MemoryStream()
        self._module.Write(ms)
        raw_bytes = ms.ToArray()
        datas = bytes(bytearray(raw_bytes))
        return datas

    def get_arg_signature(self, token: int):
        return self._method_args_sig[token]

    def get_local_var_sig_tok(self, local_var_sig: bytes) -> int:
        return self._sig_to_local_var_sig_tok_map[local_var_sig]
