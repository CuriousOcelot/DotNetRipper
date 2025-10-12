# .NET IL Code Capture and Editor Using WinDbg and Python

> ⚠️ **Disclaimer**: This project includes parts
> from [JITHook](https://github.com/LJP-TW/JITHook) [[https://github.com/LJP-TW/JITHook](https://github.com/LJP-TW/JITHook)] (
> especially `JITUnpacker`). Thanks to the author for the helpful resource—it was especially useful when I was stuck with
> dnlib-based editing. The executable files in the resource folder are compiled binaries of test code from [JITHook](https://github.com/LJP-TW/JITHook) .
>
> This tool is provided for educational and research purposes only.  
> The author is not responsible for any misuse or damage caused by this software.  
> Use it at your own risk.  
>
> This project does not distribute any malicious code or binaries.  
> Users must comply with all applicable laws when using this tool.  
> Reverse engineering software may be subject to legal restrictions in some jurisdictions—please ensure you have the right to analyze the target binaries.

# ⚠️ Warning

Executable (.exe) files in the ```/rsc/jit_hook_test_binary.zip``` may trigger false positive antivirus alerts.<br>
That is why ```/rsc/jit_hook_test_binary.zip``` is zipped with password. Password is ```password```<br>
If you do not trust this project or its author, do in a virtual machine (e.g., VirtualBox). <br>
The executable files in ```/rsc/jit_hook_test_binary.zip``` are compiled binaries of test code from [JITHook](https://github.com/LJP-TW/JITHook) .

---

## 📌 Context

When analyzing .NET malware samples, you may find that method bodies are missing during static analysis. This is because
such samples often load their IL code dynamically at runtime, rendering tools like `dnspy` is ineffective.

Traditional methods such as JIT hooking (intercepting `compileMethod` and `getEHinfo`) can help, but many malware
samples behave differently or fail to run properly when runtime binaries are modified via trampoline hooks.

To work around this, **WinDbg** can be used to **debug** and **dump the necessary memory**, allowing to capture the
arguments and results of these functions **without modifying the process**.

## 🤔 Why Python?

Most .NET reverse engineering tools are written in C# and are part of old or complex Visual Studio projects. Compiling them is difficult, and Visual Studio is bloated for small tasks.

I ❤️ Python — it's lightweight, easy to use. So, this tool was written in Python for simplicity.

---

## ✅ Tested in x64 binaries — ❌ Not Yet in x86 binaries but should work

## 📋 Features

- Capture arguments passed to `CILJit::compileMethod` and the result of `IMethodInfo::getEhInfo` using WinDbg.
- Reconstruct packed `.exe` or `.dll` using the captured IL code and metadata.
- No JIT hooking is needed to retrieve method body, as we directly read memory using WinDbg.
- Fully scriptable and customizable.

---

## 🧠 Workflow Overview

### Step 1: Capture IL Code

Use WinDbg to attach to the target .NET process and log the parameters and results of key JIT functions.

➡️ **Read `WINDBG_STEP.md`** for step-by-step instructions.

### Step 2: Modify Executable

Once the IL and metadata are captured, use the Python script to patch existing IL methods

---

## 🧪 Quick Testing

To test the full process, run:

```bat
.\setup.bat
.\test_unpack.bat
```

This will:
- Extract `.\rsc\jit_hook_test_binary.zip` to `.\rsc\jit_hook_test_binary\`. Zip password is ```password```
- Use `packed_*.exe` from `.\rsc\jit_hook_test_binary\test_binary_x64\`
- Unpack it in bytes data and calculate the checksums
- Verify the checksums matches the known `unpacked_*.exe` binaries.

Or manually run:

```bat
.\main_dotnet_editor.bat
```

This will unpack:

```plaintext
.\rsc\jit_hook_test_binary\test_binary_x64\packed_testprog.exe
```

to:

```plaintext
~\Downloads\unpacked_testprog.exe
```

using the debug data from:

```plaintext
.\rsc\jit_hook_test_binary\windebug_output\
```

---

## 🛠️ Command Line Usage

```bash
(.venv) > python ./main_dotnet_editor.py -i "input_path" -o "output_path" -w "windbug_output_path" -f "folder_name_in_windebug_output_path"
```
## Command Line Arguments

The tool supports the following command line options:

| Argument                     | Description                          | Type  | Default            |
|------------------------------|--------------------------------------|-------|--------------------|
| `-i`, `--input`              | Input file path                      | `str` | *packed_testprog.exe* |
| `-o`, `--output`             | Output file path                     | `str` | *un_testprog.exe*  |
| `-w`, `--windebug`           | WinDbg output file path              | `str` | *windbg_output*    |
| `-f`, `--folder_name`        | Subfolder name in WinDbg output path | `str` | *input file name*  |
| `-y`, `--yes`                | Skip prompt (assume yes)             | Flag  | `False`            |
| `-t`, `--testmode`           | Enable test mode                     | Flag  | `False`                |


## ✅ Requirements

- Python 3.x
- WinDbg (for initial data capture)

---

## Credits

- JITPacker and it's test executable files are from [JITHook](https://github.com/LJP-TW/JITHook) [[https://github.com/LJP-TW/JITHook](https://github.com/LJP-TW/JITHook)].

---



