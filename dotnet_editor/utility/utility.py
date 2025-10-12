import hashlib
import logging
import os

from dotnet_editor.utility.logger_util_no_line_num import getlogger_no_line_num


def hex_list_to_unsigned_int_list(hex_list):
    return [int(h, 16) for h in hex_list]


def hex_list_to_bytes(hex_list):
    return bytes(int(h, 16) for h in hex_list)


def int_to_hex(int_value):
    return f"0x{int_value:08X}"


def uint_to_hex(int_value):
    return f"0x{int_value:02X}"


def int_list_to_hex_list(int_list):
    return [f"0x{h:02X}" for h in int_list]


def bytes_to_hex_list(byte_data):
    return [f"0x{b:02X}" for b in byte_data]


logger_with_no_line_num = getlogger_no_line_num(__name__, logging.DEBUG)


def debug_logging_with_no_line_num(text: str):
    logger_with_no_line_num.debug(text)


def info_logging_with_no_line_num(text: str, extra=None):
    if extra is None:
        extra = {}
    logger_with_no_line_num.info(text, extra=extra)


def error_logging_with_no_line_num(text: str):
    logger_with_no_line_num.error(text)


def sha256sum(filename):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def sha256sum_bytes(data: bytearray) -> str:
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()


def sha1sum(filename):
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha1.update(chunk)
    return sha1.hexdigest()


def sha1sum_bytes(data: bytearray) -> str:
    sha1 = hashlib.sha1()
    sha1.update(data)
    return sha1.hexdigest()


def is_folder_empty_of_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        if files:  # If any file is found
            return False
    return True
