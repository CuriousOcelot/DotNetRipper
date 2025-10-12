


@echo off
set "DLL_FILE=packed_testprog.exe"
set "INPUT_EXE=%~dp0rsc\jit_hook_test_binary\test_binary_x64\%DLL_FILE%"
set "OUT_PATH=%USERPROFILE%\Downloads\un%DLL_FILE%"
set "WIN_DEBUG_OUTPUT=%~dp0rsc\jit_hook_test_binary\windbg_output"



set PYTHONPATH=%PYTHONPATH%;"%~dp0"
cd "%~dp0"
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
%PYTHON_EXE% ./main_dotnet_editor.py -i "%INPUT_EXE%" -o "%OUT_PATH%" -w "%WIN_DEBUG_OUTPUT%"
echo %PYTHON_EXE% ./main_dotnet_editor.py -i "%INPUT_EXE%" -o "%OUT_PATH%" -w "%WIN_DEBUG_OUTPUT%"
timeout 30