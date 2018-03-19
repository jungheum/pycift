"""pycift.common_defines

    * Description
        Common defines for pycift modules
"""
import logging
from ctypes import *
from enum import Enum, IntEnum
import inspect

# ===================================================================
# DEBUGGING FLAGS
#
CIFT_DEBUG = False
# CIFT_DEBUG = True
CIFT_DEBUG_CLOUD = False
# CIFT_DEBUG_CLOUD = True


# ===================================================================
# STATIC FUNCTIONS
#
# GET_MY_NAME = lambda: inspect.stack()[1][3]  # Method name only
def GET_MY_NAME():
    stack = inspect.stack()
    the_class  = stack[1][0].f_locals["self"].__class__.__name__
    the_method = stack[1][0].f_code.co_name
    return "{}.{}".format(str(the_class), the_method)


# ===================================================================
# GLOBAL LOGGING POLICY
#
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d    %(name)-38s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def init_progress_log():
    """Initialize the progress log file
    """
    root_logger = logging.getLogger()

    for h in root_logger.handlers:
        if isinstance(h, logging.FileHandler):
            root_logger.removeHandler(h)

    file_handler = logging.FileHandler("last_progress_log.txt", mode='w', encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d    %(name)-38s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    return


init_progress_log()


# ===================================================================
# ENUMERATIONS
#
class CIFTOperation(IntEnum):
    """CIFTOperation class
    """
    # IoT device itself
    HARDWARE = 0x00000000
    HARDWARE_FILES = 0x00000001
    HARDWARE_RAM = 0x00000002

    # IoT cloud service
    CLOUD = 0x00000011

    # IoT companion devices (applications)
    COMPANION = 0x00000100
    COMPANION_APP_ANDROID = 0x00000101
    COMPANION_APP_IOS = 0x00000102

    COMPANION_BROWSER_CHROME = 0x00001001

    COMPANION_RAM = 0x00010000
    COMPANION_RAM_ANDROID = 0x00010001
    # COMPANION_RAM_WINDOWS = 0x00010002
    # COMPANION_RAM_OSX = 0x00010003


class CIFTBrowserDrive(IntEnum):
    """CIFTBrowserDrive class
    """
    PHANTOMJS = 0x00000001  # Phantomjs
    CHROME    = 0x00000002  # Chrome drive
    # FIREFOX   = 0x00000003  # Firefox drive (NOT YET)


class CIFTOption(IntEnum):
    """CIFTOption class
    """
    DOWNLOAD_VOICE_DATA = 0x00000001


# ===================================================================
# GLOBAL STRINGS
#
EVIDENCE_LIBRARY = "Evidence_Library"

CIFT_AMAZON_ALEXA = "cift_amazon_alexa"
CIFT_GOOGLE_ASSISTANT = "cift_google_assistant"

RESULT_DB_AMAZON_ALEXA = CIFT_AMAZON_ALEXA + ".db"
RESULT_DB_GOOGLE_ASSISTANT = CIFT_GOOGLE_ASSISTANT + ".db"

INPUT_ENABLED = "enabled"
INPUT_CLOUD = "cloud"
INPUT_CLOUD_CRED_IDPW = "credential_idpw"
INPUT_CLOUD_CRED_COOKIE = "credential_cookie"
INPUT_CLIENT = "client"
INPUT_CLIENT_ANDROID = "android_app"
INPUT_CLIENT_IOS = "ios_app"
INPUT_CLIENT_CHROMIUM = "chromium_main-disk-cache"

PREFIX_ALEXA_API = "https://alexa."
PREFIX_ALEXA_API_ALTERNATIVES = ["https://pitangui."]


# ===================================================================
# SIGNATURES AND STRUCTURES
#
SIG_CHROMIUM_SIMPLE_CACHE_INITIAL_MAGIC = b'\x30\x5C\x72\xA7\x1B\x6D\xFB\xFC'
SIG_CHROMIUM_SIMPLE_CACHE_EOS_MAGIC = b'\xD8\x41\x0D\x97\x45\x6F\xFA\xF4'
SIG_GZIP = b'\x1F\x8B'
SIG_JPEG = b'\xFF\xD8\xFF'
SIG_PNG = b'\x89\x50\x4E\x47'
SIG_JPEG = b'\xFF\xD8\xFF'
SIG_SQLITE = b'SQLite format 3'
SIG_GIF = b'GIF89a'
SIG_XML = b'<?xml'
SIG_BINARYCOOKIE = b'cook'
SIG_JSON = b'{"'
SIG_MP4 = b'ftyp'
SIG_MP3 = b'\xFF\xF3'

