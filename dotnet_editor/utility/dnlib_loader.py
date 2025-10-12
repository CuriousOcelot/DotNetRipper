import logging

import clr
from config import PATH_TO_DNLIB_DLL, PATH_TO_DNLIB_DLL_ALTERNATE
from functools import lru_cache

from dotnet_editor.utility.logger_util import getlogger

logger = getlogger(__name__, logging.DEBUG)


@lru_cache(maxsize=1)
def load_dnlib():
    try:
        clr.AddReference(PATH_TO_DNLIB_DLL)
        logger.info("Loaded dnlib")
    except Exception:
        logger.error(f"Failed to load dnlib DLL from: {PATH_TO_DNLIB_DLL}")
        logger.info(f"Trying alternate \"dnlib.dll\" at {PATH_TO_DNLIB_DLL_ALTERNATE}")
        clr.AddReference(PATH_TO_DNLIB_DLL_ALTERNATE)
