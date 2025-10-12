import os.path
import re
from pathlib import Path

PROJECT_PATH = str(Path(__file__).parent.absolute())
RESOURCE_PATH = os.path.join(PROJECT_PATH, 'rsc')
TMP_PATH = os.path.join(PROJECT_PATH, 'tmp')
os.makedirs(RESOURCE_PATH, exist_ok=True)
os.makedirs(TMP_PATH, exist_ok=True)

PATH_TO_DNLIB_DLL = str(os.path.join(RESOURCE_PATH, "lib", "dnlib_4_5_0", "dnlib.dll"))
PATH_TO_DNLIB_DLL_ALTERNATE = str(os.path.join(RESOURCE_PATH, "lib", "dnlib_3_5_0", "dnlib.dll"))

# Lets read the "WINDBG_PY_VERSION"
PARSED_WINDBG_PY_VERSION = None
windbg_py_path = os.path.join(PROJECT_PATH, "windbg.py")
with open(windbg_py_path, 'r') as f:
    content = f.read()
    match = re.search(r'WINDBG_PY_VERSION\s*=\s*\"(\d+\.\d+\.\d+)\"', content)
    if match:
        PARSED_WINDBG_PY_VERSION = match.group(1)

if PARSED_WINDBG_PY_VERSION is None:
    raise Exception("Cannot parse WINDBG_PY_VERSION from \"windbg.py\"")
