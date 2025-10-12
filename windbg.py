WINDBG_PY_VERSION = "1.2.1"  # Set up this script version

import os
import json
import hashlib
import re
import struct
import sys
import time

import pykd

#    ██    ██ ███████ ██████  ███████ ██  ██████  ███    ██      ██████ ██   ██ ███████  ██████ ██   ██
#    ██    ██ ██      ██   ██ ██      ██ ██    ██ ████   ██     ██      ██   ██ ██      ██      ██  ██
#    ██    ██ █████   ██████  ███████ ██ ██    ██ ██ ██  ██     ██      ███████ █████   ██      █████
#     ██  ██  ██      ██   ██      ██ ██ ██    ██ ██  ██ ██     ██      ██   ██ ██      ██      ██  ██
#      ████   ███████ ██   ██ ███████ ██  ██████  ██   ████      ██████ ██   ██ ███████  ██████ ██   ██
#
#
# First lets check python version
required_python_version = (3, 12, 5)
current_version = sys.version_info

if current_version < required_python_version:
    required_version_str = ".".join(map(str, required_python_version))
    print(f"Python version is: {current_version.major}.{current_version.minor}.{current_version.micro} | required >= {required_version_str}")
    print(f"Please upgrade because we did not test below {required_version_str}")
    input("Press Enter to continue...")

#     ██████   ██████  ██      ██████   █████  ██          ██    ██  █████  ██████
#    ██       ██    ██ ██      ██   ██ ██   ██ ██          ██    ██ ██   ██ ██   ██
#    ██   ███ ██    ██ ██      ██████  ███████ ██          ██    ██ ███████ ██████
#    ██    ██ ██    ██ ██      ██   ██ ██   ██ ██           ██  ██  ██   ██ ██   ██
#     ██████   ██████  ███████ ██████  ██   ██ ███████       ████   ██   ██ ██   ██
#
#
# Use list or dict in global var not to produce bugs
# in aceesing in functons also
DUMPED_DETAIL = []
GLOBAL_VAR_MAP = {"dump_sequence_counter": 0}

#    ███████ ███████ ████████ ██    ██ ██████
#    ██      ██         ██    ██    ██ ██   ██
#    ███████ █████      ██    ██    ██ ██████
#         ██ ██         ██    ██    ██ ██
#    ███████ ███████    ██     ██████  ██
#
#

print(f"\n{'#' * 50}\n")
# Now lets extract the arguyment to determine windebug output folder
peb_output = pykd.dbgCommand("!peb")
first_argument = None
for line in peb_output.splitlines():
    if "CommandLine" in line:
        try:
            splited_by_quotes = re.split(r"[\"']", line.strip())
            first_argument = splited_by_quotes[1].split()[1].strip()
        except:
            pass
        break

if first_argument is not None:
    LOADED_MODULE_NAME = os.path.basename(first_argument).strip()
    print("Loaded module: ", LOADED_MODULE_NAME)
    print("Full path: ", first_argument)
    folder_to_store = os.path.splitext(os.path.basename(first_argument))[0]
    folder_to_store = re.sub(r'[<>:"/\\|?*]', '_', folder_to_store)
    windbg_output = os.path.join(os.path.expanduser('~'), "Downloads", 'windbg_output', folder_to_store)
else:
    print("Please pass argument in to the Loader.")
    sys.exit()
os.makedirs(windbg_output, exist_ok=True)
print(f"Storing result at: {windbg_output}")
print(f"\n{'#' * 50}\n")

# Make small delay to check details which is printed
delay_sec = 10
print(f"Starting in {delay_sec} seconds...")
for i in reversed(range(delay_sec)):
    print(i)
    time.sleep(1)

#    ███    ███  ██████  ██████  ███████ ██      ███████
#    ████  ████ ██    ██ ██   ██ ██      ██      ██
#    ██ ████ ██ ██    ██ ██   ██ █████   ██      ███████
#    ██  ██  ██ ██    ██ ██   ██ ██      ██           ██
#    ██      ██  ██████  ██████  ███████ ███████ ███████
#
#

# I dont know if CORINFO_SIG_INFO_FORMAT is correct
CORINFO_SIG_INFO_FORMAT = struct.Struct('<' + (
        'Q' +  # callConv
        'Q' +  # retTypeClass
        'Q' +  # retTypeSigClass
        'Q' +  # retType_flags_numArgs
        'Q' +  # sigInst0
        'Q' +  # sigInst1
        'Q' +  # sigInst2
        'Q' +  # sigInst3
        'Q' +  # args
        'Q' +  # pSig (void*, uint8_t*)
        'I' +  # cbSig (uint32_t*)
        'I' +  # ????? I cant confirm corectnes
        'Q' +  # scope (void*) ??? I cant confirm corectnes
        'Q'  # token (uint32_t*)  ??? I cant confirm corectnes
))


#    ███    ███ ███████ ████████ ██   ██  ██████  ██████  ███████
#    ████  ████ ██         ██    ██   ██ ██    ██ ██   ██ ██
#    ██ ████ ██ █████      ██    ███████ ██    ██ ██   ██ ███████
#    ██  ██  ██ ██         ██    ██   ██ ██    ██ ██   ██      ██
#    ██      ██ ███████    ██    ██   ██  ██████  ██████  ███████
#
#


def read_signature(cisi_data_struct):
    # Hmmm.... could not use to make new CORINFO_SIG_INFO_FORMAT here
    # so, pass it as argument as "cisi_data_struct"
    if cisi_data_struct[9] == 0:  # this may say no local variable
        cisi_sigbytes_hex = []
    else:
        cisi_real_sig_addr = cisi_data_struct[9]
        cisi_real_sig_len = cisi_data_struct[10]
        cisi_sig_bytes = pykd.loadBytes(cisi_real_sig_addr, cisi_real_sig_len)
        cisi_sigbytes_hex = [f"0x{b:02X}" for b in cisi_sig_bytes]
    return cisi_sigbytes_hex


def extract_module_address(os_module, domain_dumps: str, module_name_with_extension: str):
    splited = domain_dumps.splitlines()
    modules_addrs = []
    for s in splited:
        if module_name_with_extension in s:
            s = s.strip()
            possible_hex = s[:16]
            try:
                int(possible_hex, 16)
            except ValueError:
                continue
            possible_path_st = s[16:].strip()
            modules_addres = {
                "addr": possible_hex,
                "name": os_module.path.basename(possible_path_st)
            }
            modules_addrs.append(modules_addres)
    return modules_addrs


def parse_ftn_dump(dump_str):
    result = {}
    for line in dump_str.strip().splitlines():
        if ":" in line:
            key, value = line.split(": ", 1)
            result[key.strip()] = value.strip()
    return result


#    ███████ ███████ ████████     ██████  ██████  ███████  █████  ██   ██ ██████   ██████  ██ ███    ██ ████████ ███████
#    ██      ██         ██        ██   ██ ██   ██ ██      ██   ██ ██  ██  ██   ██ ██    ██ ██ ████   ██    ██    ██
#    ███████ █████      ██        ██████  ██████  █████   ███████ █████   ██████  ██    ██ ██ ██ ██  ██    ██    ███████
#         ██ ██         ██        ██   ██ ██   ██ ██      ██   ██ ██  ██  ██      ██    ██ ██ ██  ██ ██    ██         ██
#    ███████ ███████    ██        ██████  ██   ██ ███████ ██   ██ ██   ██ ██       ██████  ██ ██   ████    ██    ███████
#
#

try:
    pykd.dbgCommand("bc *")  # Clear any existing breakpoints

    clrjit_base = pykd.dbgCommand("lm m clrjit").split('\n')[2].split(" ")[0].replace("`", "")
    clrjit_base_address = int(clrjit_base, 16)
    print(f"clrjit.dll address: {hex(clrjit_base_address)}")

    clr_base = pykd.dbgCommand("lm m clr").split('\n')[2].split(" ")[0].replace("`", "")
    clr_base_address = int(clr_base, 16)
    print(f"clr.dll address: {hex(clr_base_address)}")

    # Set a memory access breakpoint on the method entry point
    bp_addr_compile_method = f"{hex(clrjit_base_address + 0x7a6e0)}"

    pykd.dbgCommand(f"ba e1 {bp_addr_compile_method}")  # Adjust as necessary for your clrjit base
    print(f"[+] Breakpoint set at CILJit::compileMethod [{bp_addr_compile_method}]")

    # bp_addr_rtn_get_ehinfo = f"{hex(clr_base_address+ 0x4FBF8)}" # at return of clr base
    # bp_addr_rtn_get_ehinfo = f"{hex(clrjit_base_address+ 0x72E31)}" #before getEHinfo excecuted
    # bp_addr_rtn_get_ehinfo = f"{hex(clrjit_base_address+ 0x72E37)}" #after getEHinfo excecuted

    bp_addr_rtn_get_ehinfo = f"{hex(clrjit_base_address + 0x72E31)}"  # before getEHinfo excecuted
    bp_addr_rtn_get_ehinfo_after_step_over = f"{hex(clrjit_base_address + 0x72E31 + 0x06)}"

    pykd.dbgCommand(f"ba e1 {bp_addr_rtn_get_ehinfo}")  # Adjust as necessary for your clrjit base
    print(f"[+] Breakpoint set at return of IMethodInfo::getEhInfo [{bp_addr_rtn_get_ehinfo}]")
except Exception as e:
    print(f"[!] Failed to set breakpoint: {e}")
    print("Exiting....")
    exit(1)

#    ██      ███████ ████████ ███████     ███████ ████████  █████  ██████  ████████
#    ██      ██         ██    ██          ██         ██    ██   ██ ██   ██    ██
#    ██      █████      ██    ███████     ███████    ██    ███████ ██████     ██
#    ██      ██         ██         ██          ██    ██    ██   ██ ██   ██    ██
#    ███████ ███████    ██    ███████     ███████    ██    ██   ██ ██   ██    ██
#
#
# Loop until process exits or exception occurs
while True:
    try:
        try:
            pykd.go()  # This might throw the HRESULT error
        except Exception as e:
            if "SetExecutionStatus failed" in str(e) or "0x80004002" in str(e):
                print(f"[!] Breaking loop: {e}")
                break
            else:
                raise e  # Re-raise other unexpected exceptions
        # If we get here, the breakpoint was hit
        ip = pykd.reg("rip")
        bp_rip_addr = f"{hex(ip)}"
        if bp_rip_addr == bp_addr_compile_method:
            print("Hit at CILJit::compileMethod")
            flag_hit_at_compileMethod = True
        elif bp_rip_addr == bp_addr_rtn_get_ehinfo:
            print("Hit at return of IMethodInfo::getEhInfo")
            flag_hit_at_compileMethod = False
        else:
            print(f"******** UNKNOWN BREAKPOINT [{bp_rip_addr}]********")
            print(f"Wait for some 3 seconds...")
            time.sleep(1)  # Exceptions might trigger breakpoit... so continue after some wait
            continue
        if flag_hit_at_compileMethod:  # when compileMethod is hitted
            corinfo_method_info_addr = pykd.reg("r8")  # Second parameter is in r8

            # Offsets from CORINFO_METHOD_INFO structure # total 256 bytes
            # struct CORINFO_METHOD_INFO
            # {
            #     CORINFO_METHOD_HANDLE ftn;     // +0x00 (8)
            #     CORINFO_MODULE_HANDLE scope;   // +0x08 (8)
            #     uint8_t *ILCode;               // +0x10 (8)
            #     unsigned ILCodeSize;           // +0x18 (4)
            #     unsigned maxStack;             // +0x1C (4)
            #     unsigned EHcount;              // +0x20 (4)
            #     CorInfoOptions options;        // +0x24 (4)
            #     CorInfoRegionKind regionKind;  // +0x28 (4)
            #     // Padding to align next field (CORINFO_SIG_INFO, 8-byte aligned)
            #     uint32_t pad;                  // +0x2C (4) padding
            #     CORINFO_SIG_INFO args;         // +0x30 (0x68)
            #     CORINFO_SIG_INFO locals;       // +0x98 (0x68)
            # }; // Total: **0x100 (256 bytes)**

            addr_ftn = corinfo_method_info_addr + 0x00  # pointer (8)
            # addr_scope = corinfo_method_info_addr + 0x08  # pointer (8)
            addr_il_codes_pointer = corinfo_method_info_addr + 0x10  # pointer (8)
            addr_il_code_size = corinfo_method_info_addr + 0x18  # value (4)

            addr_max_stack = corinfo_method_info_addr + 0x1C  # value (4)
            addr_eh_count = corinfo_method_info_addr + 0x20  # value (4)
            # addr_options = corinfo_method_info_addr + 0x24  # value (4)
            # addr_region_kind = corinfo_method_info_addr + 0x28  # value (4) # after this padding  (4)
            addr_args = corinfo_method_info_addr + 0x30  # value 104 bytes  (104)
            addr_locals = corinfo_method_info_addr + 0x98  # value 104 bytes (104)

            # Fetch method info from memory

            # Read pointer from R8 (CORINFO_METHOD_INFO*)
            addr_ftn_handle = pykd.ptrPtr(addr_ftn)
            print("[*] R8 points to CORINFO_METHOD_INFO at: 0x{:016X}".format(corinfo_method_info_addr))
            print("[*] MethodDesc (ftn) pointer: 0x{:016X}".format(addr_ftn_handle))
            # Let's just use the !dump command — reading directly from memory is hard and error-prone
            dumpmd_command = "!dumpmd 0x{:016X}".format(addr_ftn_handle)
            ftn_dumps_str = pykd.dbgCommand(dumpmd_command)
            try:
                ftn_dumps_map = parse_ftn_dump(ftn_dumps_str)
            except Exception as e:
                print(f"Unable to parse dump: {ftn_dumps_str}")
                sys.exit()

            # scope_value_addr = pykd.loadQWords(addr_scope, 1)[0]
            # scope_bytes = pykd.loadBytes(scope_value_addr, 8)
            # scope_hex = [f"0x{b:02X}" for b in scope_bytes]

            # il codes
            il_codes_pointer_value = pykd.loadQWords(addr_il_codes_pointer, 1)[0]
            il_code_size = pykd.loadDWords(addr_il_code_size, 1)[0]  # 4-byte unsigned integer
            il_codes = pykd.loadBytes(il_codes_pointer_value, il_code_size)
            il_codes_hex = [f"0x{b:02X}" for b in il_codes]

            # max stacks
            max_stack = pykd.loadDWords(addr_max_stack, 1)[0]  # 4-byte unsigned integer
            # eh_count
            eh_count = pykd.loadDWords(addr_eh_count, 1)[0]  # 4-byte unsigned integer
            # options
            # options = pykd.loadDWords(addr_options, 1)[0]  # 4-byte unsigned integer
            # region kind
            # region_kind = pykd.loadDWords(addr_region_kind, 1)[0]  # 4-byte unsigned integer

            # args sig
            args_bytes = pykd.loadBytes(addr_args, 0x68)
            args_sig_bytes_hex = read_signature(CORINFO_SIG_INFO_FORMAT.unpack(bytes(args_bytes)))

            # local var sig
            locals_bytes = pykd.loadBytes(addr_locals, 0x68)
            lv_sig_bytes_hex = read_signature(CORINFO_SIG_INFO_FORMAT.unpack(bytes(locals_bytes)))

            detail = {
                "version": WINDBG_PY_VERSION,
                "ftn_dumps": ftn_dumps_map,
                "il_codes": il_codes_hex,
                "il_code_size": f"0x{il_code_size:02X}",
                "max_stack": f"0x{max_stack:02X}",
                "eh_count": f"0x{eh_count:02X}",
                "args_var_sig": args_sig_bytes_hex,
                "local_var_sig": lv_sig_bytes_hex,
            }
        else:
            # When getEHinfo get hitted
            ehinfo_ftn_value_addr = pykd.reg("rdx")  # First parameter is in rdxod

            # Read pointer from RDX (CORINFO_METHOD_INFO)
            print("[*] MethodDesc (ftn) pointer: 0x{:016X}".format(ehinfo_ftn_value_addr))
            # Let's just use the !dump command — reading directly from memory is hard and error-prone
            dumpmd_command = "!dumpmd 0x{:016X}".format(ehinfo_ftn_value_addr)
            ftn_dumps_str = pykd.dbgCommand(dumpmd_command)
            try:
                ftn_dumps_map = parse_ftn_dump(ftn_dumps_str)
            except Exception as e:
                print(f"Unable to parse dump: {ftn_dumps_str}")
                sys.exit()

            eh_number = pykd.reg("r8d")

            corinfo_eh_clause_addr = pykd.reg("r9")

            # now lets do step over
            pykd.dbgCommand("p")
            rip = f'{hex(pykd.reg("rip"))}'
            print(f"[+] RIP after step over: {rip}")
            print(f"[+] expected RIP addr: {bp_addr_rtn_get_ehinfo_after_step_over}")
            if bp_addr_rtn_get_ehinfo_after_step_over != rip:
                print("Error: Expected address over rip are not same")
                print("Exiting....")
                exit(1)

            eh_clause = pykd.loadBytes(corinfo_eh_clause_addr, 24)
            eh_clause_hex = [f"0x{b:02X}" for b in eh_clause]

            detail = {
                "version": WINDBG_PY_VERSION,
                "ftn_dumps": ftn_dumps_map,
                "eh_number": eh_number,
                "eh_clause": eh_clause_hex
            }
        # write the dump file for both compileMethod and getEhInfo
        dumpable_indented_bytes = json.dumps(detail, indent=4).encode(encoding='utf-8')
        # print(dumpable)
        if flag_hit_at_compileMethod:
            file_prefix = "compileMethod"
        else:
            file_prefix = "getEhInfo"
        file_to_write = os.path.join(
            windbg_output,
            f"{file_prefix}-{GLOBAL_VAR_MAP['dump_sequence_counter']}-{hashlib.sha256(dumpable_indented_bytes).hexdigest()}.json"
        )
        GLOBAL_VAR_MAP['dump_sequence_counter'] = GLOBAL_VAR_MAP['dump_sequence_counter'] + 1
        print(f"Writing dumps at : {file_to_write}")
        with open(file_to_write, "wb") as writer:
            writer.write(dumpable_indented_bytes)
        DUMPED_DETAIL.append(detail)
        if "Method Name" in ftn_dumps_map:
            print(f"Dumped {file_prefix}: {ftn_dumps_map["Method Name"]}")
        else:
            print(f"Unable to found method name in \"ftn_dumps_map\": {json.dumps(ftn_dumps_map)}")
            sys.exit()

    except Exception as e:
        print(f"Exception: {str(e)}")

#    ██████  ██    ██ ███    ███ ██████      ██████   ██████  ███    ███  █████  ██ ███    ██
#    ██   ██ ██    ██ ████  ████ ██   ██     ██   ██ ██    ██ ████  ████ ██   ██ ██ ████   ██
#    ██   ██ ██    ██ ██ ████ ██ ██████      ██   ██ ██    ██ ██ ████ ██ ███████ ██ ██ ██  ██
#    ██   ██ ██    ██ ██  ██  ██ ██          ██   ██ ██    ██ ██  ██  ██ ██   ██ ██ ██  ██ ██
#    ██████   ██████  ██      ██ ██          ██████   ██████  ██      ██ ██   ██ ██ ██   ████
#
#

dump_domain_result = pykd.dbgCommand("!DumpDomain")
module_addr_list = extract_module_address(os, dump_domain_result, LOADED_MODULE_NAME)
if len(module_addr_list) != 1:
    print(f"Error in module address extraction: {len(module_addr_list)} found")

file_to_write = os.path.join(windbg_output, "module_location.json")
print(f"Writing Module addresses at : {file_to_write}")
# Add version
with open(file_to_write, "wb") as writer:
    writer.write(
        json.dumps(
            {
                "version": WINDBG_PY_VERSION,
                "module_addr": module_addr_list,
            },
            indent=4
        ).encode("utf-8"))

# Final dump of collected data
# print(json.dumps(DUMPED_DETAIL, indent=4))
print(f"\n\n\nDumped counts: {len(DUMPED_DETAIL)}")
print("############ Everything is done. ############\n\n\n")
