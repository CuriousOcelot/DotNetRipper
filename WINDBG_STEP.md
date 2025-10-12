# WinDbg Debugging Steps

WinDbg is a powerful debugger for Windows that provides deep inspection capabilities.

## 🧰 Prerequisites

- WinDbg  
- `pykd.dll` (Python extension for WinDbg)  
- Ghidra *(optional, for analyzing binaries)*

---

## ⚙️ pykd installation step
🔹 Install `pykd` According to Your Python Version

1. Go to the `pykd` GitHub releases page:  
   [https://github.com/ivellioscolin/pykd](https://github.com/ivellioscolin/pykd)

2. Download the appropriate `.whl` file from [https://github.com/ivellioscolin/pykd-ext](https://github.com/ivellioscolin/pykd-ext)

3. Install the downloaded `.whl` file using pip:
```text
.load C:\Path\To\pykd.dll
!pip install C:\Path\To\pykd-*.whl
```

## ⚙️ Setup Instructions

1. Launch `./dll_loader/Loader.exe` with your DLL path as argument. ```WinDbg > Lauch executable (advanced)```<br>e.g., from WinDbg: ```Executable = Path\to\Loader.exe```, ```Arguments = Path\to\your.dll```

2. Load `pykd` extension in WinDbg:  
   ```text
   .load C:\path\to\pykd.dll;
   ```

3. Set a breakpoint for `clrjit.dll` load and run:  
   ```text
   sxe ld clrjit.dll; g;
   ```

4. Load interactive Python in WinDbg:  
   ```text
   !py;
   ```

5. In interactive Python, run:  
   ```python
   run = lambda path: exec(open(path).read()); run(r"C:\path\to\windbg.py"); quit();
   ```

    > You can also run everything in one line:
    ```text
    .load C:\path\to\pykd_ext_2.0.0.25_x64\pykd.dll; sxe ld clrjit.dll; g; !py;
    ```

    ```python
    run = lambda path: exec(open(path).read()); run(r"C:\path\to\windbg.py"); quit();
    ```

6. This will automatically break at `CILJit::compileMethod` and just before calling `getEHinfo`.  
   It will capture the arguments and results, saving them to:  
   ```
   ~/Downloads/windbg_output
   ```

7. ⚠️ Note: Breakpoint addresses are hardcoded and **may differ** between versions of `clrjit.dll`.

---

## 🧭 Finding Breakpoint Addresses

1. Load the DLL/EXE in Ghidra or a similar tool.  
2. Identify the target line/function and set a breakpoint where desired.  
3. Load the program and let the breakpoint hit.  
4. Get the address of the breakpoint in memory.  
5. Get the module base address in WinDbg using:  
   ```text
   lm m module_name
   ```
   Example:  
   ```text
   lm m clrjit
   ```

6. Calculate the offset by subtracting the module base address from the breakpoint address.

   Example breakpoint command:
   ```text
   ba e1 clrjit+0x7a6e0
   ```
   Here, `0x7a6e0` is the calculated offset.

---

Happy debugging! 🐞
