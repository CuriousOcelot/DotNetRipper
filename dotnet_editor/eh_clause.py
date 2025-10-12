from typing import Dict, List

from dotnet_editor.utility.utility import hex_list_to_unsigned_int_list, error_logging_with_no_line_num


class EhClause:

    def __init__(self, data: Dict, exec_seq: int):
        self.exec_seq: int = exec_seq
        self._data = data
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

        self._eh_number = self._data["eh_number"]
        self._eh_clause_hex = self._data["eh_clause"]

        self._eh_clause: List[int] = hex_list_to_unsigned_int_list(self._eh_clause_hex)

    @property
    def method_token(self):
        return self._method_token

    @property
    def method_full_name(self):
        return self._method_full_name

    @property
    def method_token_hex(self):
        return f"0x{self.method_token:08X}"

    @property
    def eh_number(self):
        return self._eh_number

    @property
    def eh_clause(self) -> List[int]:
        return self._eh_clause

    @property
    def module_address(self):
        return self._module_address

    def is_exact_same(self, eh_clause: 'EhClause'):

        if self is eh_clause:
            raise Exception("Cannot use this method because the object are same")
        keys = [
            "_method_token",
            "_module_address",
            "_method_full_name",
            "_eh_number",
            "_eh_clause_hex",
        ]
        for key in keys:
            if getattr(self, key) != getattr(eh_clause, key):
                return False
        return True

        pass
