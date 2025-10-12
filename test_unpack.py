import argparse
import io
import os.path
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

import qprompt
from tqdm import tqdm

from config import RESOURCE_PATH, PROJECT_PATH
from dotnet_editor.utility.logger_util_no_line_num import LogFormat
from dotnet_editor.utility.utility import info_logging_with_no_line_num, error_logging_with_no_line_num, is_folder_empty_of_files

"""
usage: main_dotnet_editor.py [-h] [-i INPUT] [-o OUTPUT] [-w WINDEBUG] [-f FOLDER_NAME] [-y] [-t]

Example script with custom arguments

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file path
  -o OUTPUT, --output OUTPUT
                        Output file path
  -w WINDEBUG, --windebug WINDEBUG
                        Windebug output file path
  -y, --yes             Skip prompt (assume yes)
  -t, --testmode        Enable test mode

"""

if not 'PYCHARM_HOSTED' in os.environ:
    if not sys.stdin.isatty():
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


    def console_log(msg, *args, **kwargs):
        print(msg)


    test_info_logging_with_no_line_num = test_error_logging_with_no_line_num = console_log
else:
    test_info_logging_with_no_line_num = info_logging_with_no_line_num
    test_error_logging_with_no_line_num = error_logging_with_no_line_num


class TestExecutor:
    def __init__(self, input, output, windebug_folder):
        self._input = input
        self._output = output
        self._windebug_folder = windebug_folder
        self._script_path = str(os.path.join(PROJECT_PATH, "main_dotnet_editor.py"))
        pass

    def run_script(self, extra: List[str], message="", flag_more_verbose=False) -> bool:
        args = [sys.executable, self._script_path, "-i", self._input, "-o", self._output, "-w", self._windebug_folder,
                "-y", "-t"]
        args.extend(extra)
        result = subprocess.run(args, capture_output=True, text=True)
        parent_folder_name = os.path.basename(Path(self._input).parent)
        if flag_more_verbose:
            print(result.stderr)
        if result.returncode == 200:
            test_info_logging_with_no_line_num(f".../{parent_folder_name}/{os.path.basename(self._input)} Okey [✅] {message}",
                                               extra=LogFormat.BLUE_UNDERLINE)
            # print("Output:", result.stderr)
            return True
        elif result.returncode == 404:
            test_error_logging_with_no_line_num(f".../{parent_folder_name}/{os.path.basename(self._input)} Oops [❌] {message}")
            # print("Error running script:", result.stderr)
        else:
            test_error_logging_with_no_line_num(
                f"{os.path.basename(self._input)} Oops [❌] [Unknown result code: {result.returncode}] {message}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--password', help='Password input')
    args = parser.parse_args()

    jit_hook_test_binary_folder = os.path.join(RESOURCE_PATH, "jit_hook_test_binary")
    jit_hook_test_binary_zip_path = os.path.join(RESOURCE_PATH, "jit_hook_test_binary.zip")

    if not os.path.isdir(jit_hook_test_binary_folder) and not os.path.isfile(jit_hook_test_binary_zip_path):
        print(f"No such file: {jit_hook_test_binary_zip_path}")
        sys.exit(1)

    if os.path.isdir(jit_hook_test_binary_folder):
        if is_folder_empty_of_files(jit_hook_test_binary_folder):
            shutil.rmtree(jit_hook_test_binary_folder)

    if not os.path.exists(jit_hook_test_binary_folder):
        print("\nNote: Executable (.exe) files in the \"jit_hook_test_binary.zip\" may trigger false positive antivirus alerts.")
        print("If you do not trust this project or its author, do in a virtual machine (e.g., VirtualBox).")
        print("For further details, refer to README.md.")
        print("\nZip password is \"password\"")
        if not args.password:
            zip_password = qprompt.ask_str("Password")
        else:
            zip_password = args.password
        if not args.password and not qprompt.ask_yesno(f"Start extracting \"{os.path.basename(jit_hook_test_binary_zip_path)}\"", dft="y"):
            print("Canceled extraction")
            sys.exit(0)
        with zipfile.ZipFile(jit_hook_test_binary_zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            for file in tqdm(file_list, desc="Extracting files", unit='file'):
                zip_ref.extract(file, path=RESOURCE_PATH, pwd=zip_password.encode('utf-8'))
    else:
        if not os.path.isdir(jit_hook_test_binary_folder):
            print(f"Could not extract: \"{jit_hook_test_binary_zip_path}\" to \"{jit_hook_test_binary_folder}\"")
            sys.exit(1)

    windebug_folder = os.path.join(RESOURCE_PATH, "jit_hook_test_binary", "windbg_output")
    packed_rsc_path = os.path.join(RESOURCE_PATH, "jit_hook_test_binary", "test_binary_x64")
    unpacked_rsc_path = os.path.join(RESOURCE_PATH, "jit_hook_test_binary", "test_binary_x64")


    def execute_tests(flag_more_verbose: bool):
        execution_result = True
        for file_name in os.listdir(packed_rsc_path):
            file = os.path.basename(file_name)
            if not file.endswith(".exe"): continue
            if not file.startswith("packed_"): continue
            input_full_path = os.path.join(packed_rsc_path, file)
            output_full_path = os.path.join(unpacked_rsc_path, "unpacked_" + file[7:])
            test_executer = TestExecutor(input_full_path, output_full_path, windebug_folder)
            script_result = test_executer.run_script([], "", flag_more_verbose=flag_more_verbose)
            if not script_result:
                execution_result = False
        return execution_result


    if not execute_tests(False):
        print("\nThe unpacking was failed.")
        if not sys.stdin.isatty() or qprompt.ask_yesno("Do you want to unpacked again with more verbose", dft="y"):
            execute_tests(True)

    if sys.stdin.isatty():
        input("Press Enter to exit.")

