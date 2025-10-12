from typing import Dict, List

from dotnet_editor.eh_clause import EhClause
from dotnet_editor.utility.utility import error_logging_with_no_line_num


class EhClauseGroup:
    def __init__(self, method_token):
        self._method_token = method_token
        self._eh_clauses: Dict[int, EhClause] = {}
        pass

    @property
    def method_token(self):
        return self._method_token

    def add_eh_clause(self, eh_clause: EhClause):
        if eh_clause.eh_number in self._eh_clauses:
            if self._eh_clauses[eh_clause.eh_number].is_exact_same(eh_clause):
                return
            else:
                error_logging_with_no_line_num(f"Eh number: {eh_clause.eh_number} already exists and are not same | {eh_clause.method_full_name} | {hex(eh_clause.method_token)}")
                raise Exception("EhClause already exists")
        self._eh_clauses[eh_clause.eh_number] = eh_clause

    def to_bytes(self):
        eh_clause_count = len(self._eh_clauses)
        data_int_list: List[int] = []
        if eh_clause_count > 699050:
            error_logging_with_no_line_num(f"Too many exception handlers -> method token: {hex(self._method_token)}")
            raise Exception(f"Too many exception handlers.")
        if self._need_fat_exception_clauses():
            flag = (eh_clause_count * 24 + 4 << 8 | 65).to_bytes(4, byteorder='little')
            data_int_list.extend(flag)
            flag_need_fat_exception_clause = True
        else:
            flag = (eh_clause_count * 12 + 4 << 8 | 1).to_bytes(4, byteorder='little')
            data_int_list.extend(flag)
            flag_need_fat_exception_clause = False

        sorted_eh_clauses = dict(sorted(self._eh_clauses.items()))

        for key, _eh_clause in sorted_eh_clauses.items():
            flag_ehclause_is_fat = not self._is_fit_in_small_exception_clause(_eh_clause)
            if flag_need_fat_exception_clause != flag_ehclause_is_fat:
                error_logging_with_no_line_num(f"Mistmatch eh_clause size -> method token: {hex(_eh_clause.method_token)} | eh_number: {_eh_clause.eh_number}")
                raise Exception(f"Mistmatch eh_clause size")
            data_int_list.extend(_eh_clause.eh_clause)
        return bytes(data_int_list)

    def _need_fat_exception_clauses(self):
        if len(self._eh_clauses) == 0:
            return False
        if len(self._eh_clauses) > 20:
            return True

        for eh_number, eh_clause in self._eh_clauses.items():
            if not self._is_fit_in_small_exception_clause(eh_clause):
                return True
            pass

    def _is_fit_in_small_exception_clause(self, eh_clause: EhClause):
        # WriteFatExceptionClauses in for loop it wrote 24 byte
        # by doing arrayWriter.WriteUInt32 6 time in for loop

        # WriteFatExceptionClauses in for loop it wrote 12 byte
        # by doing arrayWriter.WriteUInt16 3 time,
        # arrayWriter.WriteByte 2 time and
        # arrayWriter.WriteUInt32 one time  in for loop

        eh_clause_size = len(eh_clause.eh_clause)
        if eh_clause_size == 24:
            return False
        if eh_clause_size == 12:
            return False
        error_logging_with_no_line_num(f"Invalid eh_clause size -> method token: {hex(eh_clause.method_token)} | eh_number: {eh_clause.eh_number} | size {eh_clause_size}")
        raise Exception(f"Invalid eh_clause size.")

    def eh_count(self):
        return len(self._eh_clauses)
        pass
