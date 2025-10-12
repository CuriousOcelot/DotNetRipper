# This script will edit *.cproj file of https://github.com/LJP-TW/JITHook to set for x64 or x86
import os
import re
import sys
import xml.dom.minidom
import xml.etree.ElementTree as ET
from pathlib import Path


def get_namespace(tag):
    match = re.match(r"\{(.*)\}", tag)
    return match.group(1) if match else ""


def edit_csproj(file_path, str_new_platform_target, bool_new_prefer_32bit: bool):
    str_new_prefer_32bit = "true" if bool_new_prefer_32bit else "false"
    platforms = ["x64", "x86"]
    if str_new_platform_target not in platforms: raise Exception("Invalid platform target")
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespace_uri = get_namespace(root.tag)
    ns = {"ns": namespace_uri} if namespace_uri else {}

    ET.register_namespace("", namespace_uri)  # Preserve formatting

    flag_did_changes = False

    for prop_group in root.findall("ns:PropertyGroup", ns):
        # Update PlatformTarget
        platform_elem = prop_group.find("ns:PlatformTarget", ns)
        if platform_elem is not None:
            if platform_elem.text in platforms and platform_elem.text != str_new_platform_target:
                platform_elem.text = str_new_platform_target
                flag_did_changes = True
            # if terget found chaneg the prefer32bit
            prefer32_elem = prop_group.find("ns:Prefer32Bit", ns)
            if prefer32_elem is None:
                prefer32_elem = ET.SubElement(prop_group, f"{{{ns['ns']}}}Prefer32Bit")
            if prefer32_elem.text != str_new_prefer_32bit:
                prefer32_elem.text = str_new_prefer_32bit
                flag_did_changes = True

    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    if flag_did_changes:
        rough_string = ET.tostring(root, encoding='utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        print(f"Updated '{file_path}' successfully.")
    else:
        print(f"No changes '{file_path}'")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        script_dir = Path(os.path.realpath(os.path.expanduser(sys.argv[1])))
        platform_target = sys.argv[2]
    else:
        raise Exception("Invalid arguments")

    prefer_32bit = platform_target == "x86"
    csproj_files = list(script_dir.rglob("*.csproj"))
    print(f"Found {len(csproj_files)} .csproj file(s) in '{script_dir}'.")
    valid_cproj_files = ["JITDemo.csproj", "JITPacker.csproj", "testprog.csproj", "testprog2.csproj", "testprog2_any.csproj", "testprog_any.csproj", ]

    for csproj_file in csproj_files:
        if os.path.basename(csproj_file) not in valid_cproj_files:
            print(f"Skipping: {csproj_file}")
            continue
        edit_csproj(csproj_file, platform_target, prefer_32bit)
