import json
import os

from config import PARSED_WINDBG_PY_VERSION
from dotnet_editor.utility.utility import error_logging_with_no_line_num


class ModuleAddress:

    def __init__(self, windbg_captured_dir, folder_name, module_full_path):
        module_base_name = os.path.basename(module_full_path)
        self._module_location = str(os.path.join(windbg_captured_dir, folder_name, "module_location.json"))
        with open(self._module_location) as json_file:
            data = json.load(json_file)
        self._data_version = data["version"]
        if self._data_version != PARSED_WINDBG_PY_VERSION:
            raise Exception("ModuleAddress data version dont match with windng version")
        self._module_address = int(data["module_addr"][0]['addr'], 16)
        self._module_name = data["module_addr"][0]['name']
        if self._module_name != module_base_name:
            error_logging_with_no_line_num(f"Module name not same {self._module_name} != {module_base_name} [{module_full_path}]")
            raise Exception("ModuleAddress name dont match with module name")

        pass

    @property
    def module_address_in_memory(self):
        return self._module_address


