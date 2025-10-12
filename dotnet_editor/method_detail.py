from typing import Dict

from config import PARSED_WINDBG_PY_VERSION
from dotnet_editor.utility.utility import hex_list_to_unsigned_int_list, error_logging_with_no_line_num, hex_list_to_bytes

"""
{
    "version": WINDBG_PY_VERSION,
    "ftn_dumps": ftn_dumps,
    "il_codes": il_codes_hex,
    "il_code_size": f"0x{il_code_size:02X}",
    "max_stack": f"0x{max_stack:02X}",
    "eh_count": f"0x{eh_count:02X}",
    "args_var_sig": args_sig_bytes_hex,
    "args_result": args_sig_read_result,
    "local_var_sig": lv_sig_bytes_hex,
    "lv_result": lv_sig_read_result
}
"""


class MethodDetail:
    def __init__(self, data: Dict, exec_seq: int):
        self.exec_seq: int = exec_seq
        self._data = data
        self._data_version = self._data["version"]
        if self._data_version != PARSED_WINDBG_PY_VERSION:
            raise Exception("Capture data version dont match with windng version")
        self._ftn_dump_json = self._data["ftn_dumps"]
        self._method_token = int(self._ftn_dump_json['mdToken'], 16)
        self._module_address = int(self._ftn_dump_json['Module'], 16)
        if "Method Name" in self._ftn_dump_json:
            # name_splited = self._ftn_dump_json["Method Name"].split("(")
            name_splited = self._ftn_dump_json["Method Name"].split("(", 1)
            self._method_full_name: str = name_splited[0]
        else:
            error_logging_with_no_line_num(f"No method name found: \"{hex(self._method_token)}\"")
            raise Exception(f"No method name found.")

        self._il_codes = hex_list_to_unsigned_int_list(self._data["il_codes"])
        self._il_code_size = int(self._data["il_code_size"], 16)
        if len(self._il_codes) != self._il_code_size:
            error_logging_with_no_line_num(f"Il code size mistmatch: {self._method_full_name}")
            raise Exception(f"Il code size mistmatch.")

        self._max_stack = int(self._data["max_stack"], 16)
        self._eh_count = int(self._data["eh_count"], 16)

        # parse the signatures
        self._args_var_sig_bytes = hex_list_to_bytes(self._data["args_var_sig"])
        self._local_var_sig_bytes = hex_list_to_bytes(self._data["local_var_sig"])

    @property
    def method_full_name(self):
        return self._method_full_name

    @property
    def method_token(self):
        return self._method_token

    @property
    def method_token_hex(self):
        return f"0x{self._method_token:08X}"

    @property
    def module_address(self):
        return self._module_address

    @property
    def il_codes_size(self):
        return self._il_code_size

    @property
    def il_codes(self):
        return self._il_codes

    @property
    def max_stack(self):
        return self._max_stack

    @property
    def eh_count(self):
        return self._eh_count

    @property
    def local_var_sig_bytes(self) -> bytes:
        return self._local_var_sig_bytes

    @property
    def arg_sig_bytes(self) -> bytes:
        return self._args_var_sig_bytes

    def is_exact_same(self, method_detail: 'MethodDetail'):
        if self is method_detail:
            raise Exception("Cannot use this method because the object are same")
        keys = ["_data_version",
                "_method_token",
                "_module_address",
                "_method_full_name",
                "_il_codes",
                "_il_code_size",
                "_max_stack",
                "_eh_count",
                "_args_var_sig_bytes",
                "_local_var_sig_bytes"]
        for key in keys:
            if getattr(self, key) != getattr(method_detail, key):
                return False
        return True

        pass
