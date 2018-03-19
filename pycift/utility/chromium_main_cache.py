"""pycift.utility.chromium_main_cache

    * Description
        Chromium's main disk cache parser

        > This module was revised from source codes of plaso's chrome cache parser
          (https://github.com/log2timeline/plaso/blob/master/plaso/parsers/chrome_cache.py)

    * Reference
        Chromium projects (https://www.chromium.org/)
"""

import os
import logging
import construct
import re
from pycift.common_defines import *


class AddressEntry:
    """AddressEntry class
        - Interpreting an address structure used for Chrome Cache

    Attributes:
        value (int): The entered address
        block_number (int): The block number within the data file
        block_offset (int): The offset within the data file
        block_size (int): The size assigned for this data block
        filename (str): The name of the data file
        initialized (bool): If True, this cache is initialized
    """
    FILE_TYPE_SEPARATE = 0
    FILE_TYPE_BLOCK_RANKINGS = 1
    FILE_TYPE_BLOCK_256 = 2
    FILE_TYPE_BLOCK_1024 = 3
    FILE_TYPE_BLOCK_4096 = 4

    BLOCK_DATA_FILE_TYPES = [
        FILE_TYPE_BLOCK_RANKINGS,
        FILE_TYPE_BLOCK_256,
        FILE_TYPE_BLOCK_1024,
        FILE_TYPE_BLOCK_4096
    ]

    FILE_TYPE_BLOCK_SIZES = [
        0, 36, 256, 1024, 4096
    ]

    def __init__(self, address):
        """The constructor

        Args:
            address (int): A cache address
        """
        self.value = address
        self.block_number = None
        self.block_offset = None
        self.block_size = None
        self.filename = ""
        self.initialized = True if address & 0x80000000 else False

        if address == 0x00000000:
            return  # Invalid address

        file_type = ((address & 0x70000000) >> 28)

        if file_type == self.FILE_TYPE_SEPARATE:
            file_id = address & 0x0FFFFFFF
            self.filename = 'f_{0:06x}'.format(file_id)
        elif file_type in self.BLOCK_DATA_FILE_TYPES:
            file_id = ((address & 0x00FF0000) >> 16)
            self.filename = 'data_{0}'.format(file_id)
            file_block_size = self.FILE_TYPE_BLOCK_SIZES[file_type]
            self.block_number = address & 0x0000FFFF
            self.block_offset = 0x2000 + (self.block_number * file_block_size)
            self.block_size = (((address & 0x03000000) >> 24) + 1) * file_block_size


class IndexFile:
    """IndexFile class
        - Parsing the 'index' file having an index table

    Attributes:
        file_object: The file object (the current index file)
        version (str): The index file version
        creation_time (int): The timestamp
        index_table (list): The list of indexed cache entries
        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """
    SIGNATURE = 0xC103CAC3

    # FILE_HEADER = construct.Struct(
    #     'chrome_cache_index_file_header',
    #     construct.ULInt32('signature'),
    #     construct.ULInt16('minor_version'),
    #     construct.ULInt16('major_version'),
    #     construct.ULInt32('number_of_entries'),
    #     construct.ULInt32('stored_data_size'),
    #     construct.ULInt32('last_created_file_number'),
    #     construct.ULInt32('unknown1'),
    #     construct.ULInt32('unknown2'),
    #     construct.ULInt32('table_size'),
    #     construct.ULInt32('unknown3'),
    #     construct.ULInt32('unknown4'),
    #     construct.ULInt64('creation_time'),
    #     construct.Padding(208)
    # )

    FILE_HEADER = construct.Struct(
        'signature' / construct.Int32ul,
        'minor_version' / construct.Int16ul,
        'major_version' / construct.Int16ul,
        'number_of_entries' / construct.Int32ul,
        'stored_data_size' / construct.Int32ul,
        'last_created_file_number' / construct.Int32ul,
        'unknown1' / construct.Int32ul,
        'unknown2' / construct.Int32ul,
        'table_size' / construct.Int32ul,
        'unknown3' / construct.Int32ul,
        'unknown4' / construct.Int32ul,
        'creation_time' / construct.Int64ul,
        construct.Padding(208)
    )

    def __init__(self):
        """The constructor
        """
        self.file_object = None
        self.version = None
        self.creation_time = None
        self.index_table = []
        self.prglog_mgr = logging.getLogger(__name__)

    def open(self, path_file):
        """Open and process an index file

        Args:
            path_file (str): The full path of the target file

        Returns:
            True or False
        """
        # self.prglog_mgr.info("{}(): {}".format(GET_MY_NAME(), path_file))

        try:
            self.file_object = open(path_file, 'rb')
        except IOError as exception:
            self.prglog_mgr.debug("{}(): Cannot open the file ({})".format(GET_MY_NAME(), path_file))
            return False

        self.file_object.seek(0, os.SEEK_SET)
        if self.process_file_header() is False:
            return False

        self.file_object.seek(112, os.SEEK_CUR)
        self.process_index_table()
        return True

    def process_file_header(self):
        """Process the file header

        Returns:
            True or False
        """
        # self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        try:
            header = self.FILE_HEADER.parse_stream(self.file_object)
        except construct.FieldError as exception:
            self.prglog_mgr.debug("{}(): Unable to parse the file header".format(GET_MY_NAME()))
            return False

        if header.get('signature') != self.SIGNATURE:
            self.prglog_mgr.debug("{}(): Invalid signature".format(GET_MY_NAME()))
            return False

        self.version = '{0:d}.{1:d}'.format(
            header.get('major_version'), header.get('minor_version')
        )

        if self.version not in ['2.0', '2.1']:
            self.prglog_mgr.debug("{}(): Unsupported version".format(GET_MY_NAME()))
            return False

        self.creation_time = header.get('creation_time')
        return True

    def process_index_table(self):
        """Process the index table

        Returns:
            True or False
        """
        # self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        bytes4 = self.file_object.read(4)

        while len(bytes4) == 4:
            # address = construct.ULInt32('address').parse(bytes4)
            address = construct.Int32ul.parse(bytes4)
            if address > 0:
                address_entry = AddressEntry(address)
                if address_entry.filename != "":
                    self.index_table.append(address_entry)
                else:
                    self.prglog_mgr.debug("{}(): Invalid index entry {0:X}".format(GET_MY_NAME(), address))

            bytes4 = self.file_object.read(4)

    def close(self):
        """Close this object
        """
        # self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if self.file_object is not None:
            self.file_object.close()
            self.file_object = None


class MainCacheEntry:
    """MainCacheEntry class
        - A structure for storing Chromium's main disk cache entry
    """
    def __init__(self):
        """The constructor
        """
        self.hash = None
        self.next_address = None
        self.rankings_node_address = None
        self.reuse_count = None
        self.refetch_count = None
        self.state = None
        self.creation_time = None
        self.key_size = None
        self.long_key_address = None
        self.data_stream_sizes = []
        self.data_stream_addresses = []
        self.flags = None
        self.self_hash = None
        self.key = None  # Usually URL address


class DataFile:
    """DataFile class
        - Interpreting an cache data file used for Chrome Cache
        - Parsing the 'data_0~3' files having cache entries

    Attributes:
        file_object: The file object (the current index file)
        version (str): The index file version
        block_size (int): The block size
        number_of_entries (int): The number of entries
        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """
    SIGNATURE = 0xC104CAC3

    # FILE_HEADER = construct.Struct(
    #     'chrome_cache_data_file_header',
    #     construct.ULInt32('signature'),
    #     construct.ULInt16('minor_version'),
    #     construct.ULInt16('major_version'),
    #     construct.ULInt16('file_number'),
    #     construct.ULInt16('next_file_number'),
    #     construct.ULInt32('block_size'),
    #     construct.ULInt32('number_of_entries'),
    #     construct.ULInt32('maximum_number_of_entries'),
    #     construct.Array(4, construct.ULInt32('emtpy')),
    #     construct.Array(4, construct.ULInt32('hints')),
    #     construct.ULInt32('updating'),
    #     construct.Array(5, construct.ULInt32('user'))
    # )

    FILE_HEADER = construct.Struct(
        'signature' / construct.Int32ul,
        'minor_version' / construct.Int16ul,
        'major_version' / construct.Int16ul,
        'file_number' / construct.Int16ul,
        'next_file_number' / construct.Int16ul,
        'block_size' / construct.Int32ul,
        'number_of_entries' / construct.Int32ul,
        'maximum_number_of_entries' / construct.Int32ul,
        construct.Array(4, 'emtpy' / construct.Int32ul),
        construct.Array(4, 'hints' / construct.Int32ul),
        'updating' / construct.Int32ul,
        construct.Array(5, 'user' / construct.Int32ul)
    )

    def __init__(self):
        """The constructor
        """
        self.file_object = None
        self.version = None
        self.block_size = None
        self.number_of_entries = None
        self.prglog_mgr = logging.getLogger(__name__)

    def open(self, path_file):
        """Open and process a data file

        Args:
            path_file (str): The full path of the target file

        Returns:
            True or False
        """
        # self.prglog_mgr.info("{}(): {}".format(GET_MY_NAME(), path_file))

        try:
            self.file_object = open(path_file, 'rb')
        except IOError as exception:
            self.prglog_mgr.debug("{}(): Cannot open the file ({})".format(GET_MY_NAME(), path_file))
            return False

        self.file_object.seek(0, os.SEEK_SET)
        if self.process_file_header() is False:
            return False

        return True

    def process_file_header(self):
        """Process the file header

        Returns:
            True or False
        """
        # self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        try:
            header = self.FILE_HEADER.parse_stream(self.file_object)
        except construct.FieldError as exception:
            self.prglog_mgr.debug("{}(): Unable to parse the file header".format(GET_MY_NAME()))
            return False

        if header.get('signature') != self.SIGNATURE:
            self.prglog_mgr.debug("{}(): Invalid signature".format(GET_MY_NAME()))
            return False

        self.version = '{0:d}.{1:d}'.format(
            header.get('major_version'), header.get('minor_version')
        )

        if self.version not in ['2.0', '2.1']:
            self.prglog_mgr.debug("{}(): Unsupported version".format(GET_MY_NAME()))
            return False

        self.block_size = header.get('block_size')
        self.number_of_entries = header.get('number_of_entries')
        return True

    def process_cache_entry(self, address_entry):
        """Process a cache entry

        Args:
            address_entry (AddressEntry): An instance of AddressEntry

        Returns:
            A cache entry (MainCacheEntry) or None
        """
        # self.prglog_mgr.info("{}(): OFFSET({}) of {}".format(
        #     GET_MY_NAME(), address_entry.block_offset, address_entry.filename)
        # )

        self.file_object.seek(address_entry.block_offset, os.SEEK_SET)

        # CACHE_ENTRY = construct.Struct(
        #     'chrome_cache_entry',
        #     construct.ULInt32('hash'),
        #     construct.ULInt32('next_address'),
        #     construct.ULInt32('rankings_node_address'),
        #     construct.ULInt32('reuse_count'),
        #     construct.ULInt32('refetch_count'),
        #     construct.ULInt32('state'),
        #     construct.ULInt64('creation_time'),
        #     construct.ULInt32('key_size'),
        #     construct.ULInt32('long_key_address'),
        #     construct.Array(4, construct.ULInt32('data_stream_sizes')),
        #     construct.Array(4, construct.ULInt32('data_stream_addresses')),
        #     construct.ULInt32('flags'),
        #     construct.Padding(16),
        #     construct.ULInt32('self_hash'),
        #     construct.Array(address_entry.block_size - 96, construct.UBInt8('key'))
        # )

        CACHE_ENTRY = construct.Struct(
            'hash' / construct.Int32ul,
            'next_address' / construct.Int32ul,
            'rankings_node_address' / construct.Int32ul,
            'reuse_count' / construct.Int32ul,
            'refetch_count' / construct.Int32ul,
            'state' / construct.Int32ul,
            'creation_time' / construct.Int64ul,
            'key_size' / construct.Int32ul,
            'long_key_address' / construct.Int32ul,
            construct.Array(4, 'data_stream_sizes' / construct.Int32ul),
            construct.Array(4, 'data_stream_addresses' / construct.Int32ul),
            'flags' / construct.Int32ul,
            construct.Padding(16),
            'self_hash' / construct.Int32ul,
            construct.Array(address_entry.block_size - 96, 'key'/ construct.Int8ub)
        ) 

        try:
            items = CACHE_ENTRY.parse_stream(self.file_object)
        except construct.FieldError as exception:
            self.prglog_mgr.debug("{}(): Unable to parse the cache entry".format(GET_MY_NAME()))
            return None

        cache_entry = MainCacheEntry()

        cache_entry.hash = items.get('hash')
        cache_entry.next_address = AddressEntry(items.get('next_address'))
        cache_entry.rankings_node_address = AddressEntry(items.get('rankings_node_address'))
        cache_entry.reuse_count = items.get('reuse_count')
        cache_entry.refetch_count = items.get('refetch_count')
        cache_entry.state = items.get('state')
        cache_entry.creation_time = items.get('creation_time')
        cache_entry.key_size = items.get('key_size')
        cache_entry.long_key_address = items.get('long_key_address')

        cache_entry.data_stream_sizes = items.get('data_stream_sizes')
        cache_entry.data_stream_addresses = items.get('data_stream_addresses')

        for idx in range(len(cache_entry.data_stream_addresses)):
            if cache_entry.data_stream_addresses[idx] != 0x00000000:
                cache_entry.data_stream_addresses[idx] \
                    = AddressEntry(cache_entry.data_stream_addresses[idx])

        cache_entry.flags = items.get('flags')
        cache_entry.self_hash = items.get('self_hash')

        byte_array = items.get('key')
        byte_string = ''.join(map(chr, byte_array))
        cache_entry.key, _, _ = byte_string.partition('\x00')

        return cache_entry

    def close(self):
        """Close this object
        """
        # self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if self.file_object is not None:
            self.file_object.close()
            self.file_object = None


class ChromiumMainCache:
    """ChromiumMainCache class

    Attributes:
        url_pattern (str): A regular expression for storing interesting URLs only
        cache_entries (list): A list of MainCacheEntry instances
        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self):
        self.url_pattern = None
        self.cache_entries = None
        self.prglog_mgr = logging.getLogger(__name__)

    def set_url_pattern(self, pattern):
        """Set the URL pattern

        Args:
            pattern (str): A regular expression for storing interesting URLs only
        """
        self.prglog_mgr.info("{}(): \"{}\"".format(GET_MY_NAME(), pattern))

        self.url_pattern = pattern

    def parse(self, path_root):
        """Parse chrome cache entries

        Args:
            path_root (str): The full path of the target directory
        """
        self.prglog_mgr.info("{}(): Parsing cache entries in \"{}\"".format(GET_MY_NAME(), path_root))

        # Build an index table from 'index'
        path_index_file = path_root + "/index"

        if not os.path.exists(path_index_file):
            self.prglog_mgr.debug("{}(): Not found 'index' file".format(GET_MY_NAME()))
            return False

        index_file = IndexFile()
        index_file.open(path_index_file)
        index_file.close()

        if len(index_file.index_table) == 0:
            self.prglog_mgr.info("{}(): There is no indexed cache entry".format(GET_MY_NAME()))
            return False

        # Open data files
        data_files = {}
        for address_entry in index_file.index_table:
            if address_entry.filename in data_files:
                continue

            data_file = DataFile()
            if data_file.open(path_root + "/{}".format(address_entry.filename)) is False:
                data_file.close()
            else:
                data_files[address_entry.filename] = data_file

        # Process cache entries
        self.process_cache_entries(index_file.index_table, data_files)

        # Close data files
        for file_object in iter(data_files.values()):
            file_object.close()
        return True

    def process_cache_entries(self, index_table, data_files):
        """Process cache entries in data_1, data_2 and data_3

        Args:
            index_table (list): An index table object
            data_files (dict): A dictionary containing instances of DataFile
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        self.cache_entries = list()

        for address_entry in index_table:
            while address_entry.value != 0x00000000:
                data_file = data_files.get(address_entry.filename)
                if data_file is None:
                    self.prglog_mgr.debug("{}(): Missing data file {}".format(
                        GET_MY_NAME(), address_entry.filename)
                    )
                    break

                cache_entry = data_file.process_cache_entry(address_entry)
                if cache_entry is None:
                    break

                # Save this entry to the result list
                if self.url_pattern is None:
                    self.cache_entries.append(cache_entry)
                else:
                    if re.match(self.url_pattern, cache_entry.key):
                        self.cache_entries.append(cache_entry)

                address_entry = cache_entry.next_address

    def close(self):
        """Close this object
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        self.url_pattern = None
        self.cache_entries.clear()
        self.cache_entries = None

