"""pycift.utility.chromium_simple_cache

    * Description
        Chromium's simple disk cache parser

    * Reference
        Chromium projects (https://www.chromium.org/)
"""

import os
import logging
from pycift.utility.pt_utils import PtUtils
from pycift.common_defines import *


class SimpleCacheVersion(IntEnum):
    """SimpleCacheVersion class
    """
    UNKNOWN = 0x00000000
    V1      = 0x00000010  # v1
    V2      = 0x00000020  # v2 ~ v4
    V2_T1   = 0x00000021  # v2-type1
    V2_T2   = 0x00000022  # v2-type2
    V5      = 0x00000050  # v5
    V5_T1   = 0x00000051  # v5-type1
    V5_T2   = 0x00000052  # v5-type2


class CHROMIUM_SIMPLE_CACHE_HEADER(LittleEndianStructure):
    _fields_ = [
        ("magic",   c_char*8),  # '305C72A71B6DFBFC'
        ("version", c_uint),    # 1 ~ 5
        ("keysize", c_uint),    # Length of the key
        ("keyhash", c_uint),    # super_fast_hash(key)
        ("padding", c_uint)     # 0x00000000 for type2 only
    ]
    _pack_ = 4


# Structure of an EOS (End of Stream)
class CHROMIUM_SIMPLE_CACHE_EOS_V2(LittleEndianStructure):
    _fields_ = [
        ("magic",   c_char*8),  # 'D8410D97456FFAF4'
        ("flags",   c_uint),    # b(1): CRC32
        ("crc32",   c_uint)     # CRC32 of this stream (raw data)
    ]
    _pack_ = 4


# Structure of an EOS (End of Stream)
class CHROMIUM_SIMPLE_CACHE_EOS_V5(LittleEndianStructure):
    _fields_ = [
        ("magic",      c_char*8),  # 'D8410D97456FFAF4'
        ("flags",      c_uint),    # b(1): CRC32, b(2): SHA-256
        ("crc32",      c_uint),    # CRC32 of this stream (raw data)
        ("streamsize", c_uint)     # Length of this stream
    ]
    _pack_ = 4


class SimpleCacheEntry:
    """SimpleCacheEntry class
        - A structure for storing Chromium's simple disk cache entry
    """
    def __init__(self):
        """The constructor
        """
        self.version = SimpleCacheVersion.UNKNOWN
        self.key = ""  # Usually URL address
        self.streams = []
        self.crc32 = []
        self.key_sha256 = None


class ChromiumSimpleCache:
    """ChromiumSimpleCache class

    Attributes:
        cache_entry (list): A list of SimpleCacheEntry instances
        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self):
        self.cache_entry = []
        self.prglog_mgr = logging.getLogger(__name__)

    def parse(self, file_path):
        """Parse chrome cache entries

        Args:
            file_path (str): The full path of the target file
        """
        self.prglog_mgr.info("{}(): Parsing cache entries in \"{}\"".format(GET_MY_NAME(), file_path))

        file_size = os.path.getsize(file_path)

        if file_size < sizeof(CHROMIUM_SIMPLE_CACHE_HEADER) * 2:
            self.prglog_mgr.debug("{}(): Invalid simple disk cache format".format(GET_MY_NAME()))
            return False

        try:
            file_object = open(file_path, 'rb')
        except IOError as exception:
            self.prglog_mgr.debug("{}(): Exception occurred".format(GET_MY_NAME()))
            return False

        data = file_object.read()
        file_object.close()

        offset = 0
        header = PtUtils.static_cast(
            data[offset: offset + sizeof(CHROMIUM_SIMPLE_CACHE_HEADER)],
            CHROMIUM_SIMPLE_CACHE_HEADER
        )

        if header.magic != SIG_CHROMIUM_SIMPLE_CACHE_INITIAL_MAGIC:
            self.prglog_mgr.debug("{}(): Unknown signature ({})".format(GET_MY_NAME(), header.magic))
            return False

        # Create an instance
        self.cache_entry = SimpleCacheEntry()

        # Check the format version
        if header.version == 1:
            self.cache_entry.version = SimpleCacheVersion.V1
        elif (2 <= header.version <=4) and header.padding != 0:
            self.cache_entry.version = SimpleCacheVersion.V2_T1
        elif (2 <= header.version <= 4) and header.padding == 0:
            self.cache_entry.version = SimpleCacheVersion.V2_T2
        elif 5 <= header.version and header.padding != 0:
            self.cache_entry.version = SimpleCacheVersion.V5_T1
        elif 5 <= header.version and header.padding == 0:
            self.cache_entry.version = SimpleCacheVersion.V5_T2
        else:
            self.prglog_mgr.debug("{}(): Unknown version ({})".format(GET_MY_NAME(), header.version))
            return False

        # Skip the header area
        if self.cache_entry.version == SimpleCacheVersion.V2_T2 or \
           self.cache_entry.version == SimpleCacheVersion.V5_T2:
            offset += sizeof(CHROMIUM_SIMPLE_CACHE_HEADER)
        else:
            offset += (sizeof(CHROMIUM_SIMPLE_CACHE_HEADER) - 4)

        # Get the key
        self.cache_entry.key = data[offset: offset + header.keysize].decode("utf-8")
        offset += header.keysize

        # Parse the data area (v1)
        if self.cache_entry.version == SimpleCacheVersion.V1:
            stream = data[offset:]
            self.cache_entry.streams.append(stream)

        # Parse the data area (v2 ~ v4)
        elif (self.cache_entry.version & SimpleCacheVersion.V2) == SimpleCacheVersion.V2:
            offset_saved = offset
            offset = file_size - sizeof(CHROMIUM_SIMPLE_CACHE_EOS_V2)
            eos = PtUtils.static_cast(data[offset:], CHROMIUM_SIMPLE_CACHE_EOS_V2)

            if eos.magic != SIG_CHROMIUM_SIMPLE_CACHE_EOS_MAGIC:
                self.prglog_mgr.debug("{}(): Invalid EOS".format(GET_MY_NAME()))
                self.cache_entry.crc32.append(None)
                stream = data[offset_saved:]
                self.cache_entry.streams.append(stream)

            else:
                self.cache_entry.crc32.append(eos.crc32)
                stream = data[offset_saved: file_size - sizeof(CHROMIUM_SIMPLE_CACHE_EOS_V2)]
                self.cache_entry.streams.append(stream)

        # Parse the data area (v5)
        elif (self.cache_entry.version & SimpleCacheVersion.V5) == SimpleCacheVersion.V5:
            size_of_eos = sizeof(CHROMIUM_SIMPLE_CACHE_EOS_V5)
            if self.cache_entry.version == SimpleCacheVersion.V5_T2:
                size_of_eos += 4

            # Stream 0
            offset_saved = offset
            offset = file_size - size_of_eos
            eos = PtUtils.static_cast(data[offset:], CHROMIUM_SIMPLE_CACHE_EOS_V5)

            if eos.magic != SIG_CHROMIUM_SIMPLE_CACHE_EOS_MAGIC:
                self.prglog_mgr.debug("{}(): Invalid EOS for Stream 0".format(GET_MY_NAME()))
                self.cache_entry.crc32.append(None)
                stream = data[offset_saved:]
                self.cache_entry.streams.append(stream)

            else:
                if (eos.flags & 0x00000002) == 0x00000002:
                    offset -= 32
                    self.cache_entry.key_sha256 = data[offset:offset+32]

                self.cache_entry.crc32.append(eos.crc32)
                offset -= eos.streamsize
                stream = data[offset: offset + eos.streamsize]
                self.cache_entry.streams.append(stream)

                # Stream 1
                offset -= size_of_eos
                eos = PtUtils.static_cast(data[offset:], CHROMIUM_SIMPLE_CACHE_EOS_V5)

                if eos.magic != SIG_CHROMIUM_SIMPLE_CACHE_EOS_MAGIC:
                    self.prglog_mgr.debug("{}(): Invalid EOS for Stream 1".format(GET_MY_NAME()))
                else:
                    self.cache_entry.crc32.append(eos.crc32)
                    offset -= eos.streamsize
                    stream = data[offset: offset + eos.streamsize]
                    self.cache_entry.streams.append(stream)

        return True

    def close(self):
        """Close this object
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        self.cache_entry = None

