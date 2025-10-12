import hashlib
import json
import logging
import os
from typing import Dict

from dotnet_editor.eh_clause import EhClause
from dotnet_editor.eh_clause_group import EhClauseGroup
from dotnet_editor.method_detail import MethodDetail
from dotnet_editor.module_address import ModuleAddress
from dotnet_editor.utility.logger_util import getlogger
from dotnet_editor.utility.utility import error_logging_with_no_line_num

logger = getlogger(__name__, logging.DEBUG)


class CapturedMethods:
    def __init__(self, windbg_captured_dir, folder_name, module_full_path):

        self._captured_path = str(os.path.join(windbg_captured_dir, folder_name))
        files = [f for f in os.listdir(self._captured_path) if os.path.isfile(os.path.join(self._captured_path, f))]
        self._method_details: Dict[int, MethodDetail] = {}
        self._module_address = ModuleAddress(windbg_captured_dir, folder_name, module_full_path)
        EXECUTION_SEQ=set()

        for file in files:
            base_name = os.path.basename(file)
            if not base_name.startswith("compileMethod-"): continue
            if not base_name.endswith(".json"): continue
            with open(os.path.join(self._captured_path, file), 'rb') as f:
                execution_seq = int(base_name.split("-")[1])
                if execution_seq in EXECUTION_SEQ:
                    raise Exception(f"Duplicate execution seq: {execution_seq}. Did you windbg twice???")
                EXECUTION_SEQ.add(execution_seq)
                hash_part = base_name.split('-')[2].replace('.json', '')
                content_bytes = f.read()
                calculated_hash_part = hashlib.sha256(content_bytes).hexdigest()
                if hash_part != calculated_hash_part:
                    error_logging_with_no_line_num(f"File content and hash mismatch: {base_name}")
                    raise Exception("File content and hash mismatch.")

                json_data = json.loads(content_bytes)
                method_detail = MethodDetail(json_data, execution_seq)
                if method_detail.method_token_hex == '0x06000000':  # '0x06000000' is not a valid md_token
                    continue
                if self._module_address.module_address_in_memory != method_detail.module_address:
                    # sometime two method can have same token so we need to check if the module address loaded in memory was same.
                    continue

                if method_detail.method_token in self._method_details:
                    existed_method = self._method_details[method_detail.method_token]
                    if existed_method.is_exact_same(method_detail):
                        continue  # The two method detail are same so dont ad just continue
                    else:
                        error_logging_with_no_line_num(f"Method: {method_detail.method_token_hex} already exist but content are different")
                        raise Exception(f"Method already exist but content are different")

                self._method_details[method_detail.method_token] = method_detail
                logger.info(
                    f"\n\tAdding captured method:{method_detail.method_token_hex}\n"
                    f"\tILcode_size:{method_detail.il_codes_size}\n"
                    f"\tIlcode: {' '.join([f'{i:02X}' for i in method_detail.il_codes])}"
                )

        self._eh_clause_groups: Dict[int, EhClauseGroup] = {}
        for file in files:
            base_name = os.path.basename(file)
            if not base_name.startswith("getEhInfo-"): continue
            if not base_name.endswith(".json"): continue
            with open(os.path.join(self._captured_path, file), 'rb') as f:
                execution_seq = int(base_name.split("-")[1])
                if execution_seq in EXECUTION_SEQ:
                    raise Exception(f"Duplicate execution seq: {execution_seq}. Did you windbg twice???")
                EXECUTION_SEQ.add(execution_seq)
                json_data = json.load(f)
                eh_clause = EhClause(json_data, execution_seq)
                if eh_clause.method_token_hex == '0x06000000':  # '0x06000000' is not a valid md_token
                    continue
                if self._module_address.module_address_in_memory != eh_clause.module_address:
                    # we need to check if the module address loaded in memory was same.
                    continue
                if eh_clause.method_token not in self._eh_clause_groups:
                    self._eh_clause_groups[eh_clause.method_token] = EhClauseGroup(eh_clause.method_token)
                self._eh_clause_groups[eh_clause.method_token].add_eh_clause(eh_clause)

                logger.info(
                    f"\n\tAdding EH clause for {eh_clause.method_token_hex}\n"
                    f"\tEH number: {eh_clause.eh_number}\n"
                    f"\tEh clause: {' '.join([f'{i:02X}' for i in eh_clause.eh_clause])}"
                )
        print("", flush=True)

    @property
    def method_details(self) -> Dict[int, MethodDetail]:
        return self._method_details

    def get_eh_clause_group(self, method_token):
        if method_token in self._eh_clause_groups:
            return self._eh_clause_groups[method_token]
        return EhClauseGroup(method_token)
