"""pycift.utility.pt_utils

    * Description
        PtUtils : Portable functions for Python 3 environment

    * Author
        Jungheum Park <junghmi@gmail.com>
"""

import os
import glob
import shutil
import datetime
from datetime import timezone
import dateutil.tz
import subprocess
import hashlib
import urllib
import re
import json
from ctypes import *
import gzip
import random
import iso8601


class PtUtils:
    def __init__(self):
        return

    @staticmethod
    def get_current_date_and_time(millisecond=False):
        """Get the current date & time

        Args:
            millisecond (bool): If True, the return value contains millisecond

        Returns:
            The current date (str): YYYY-MM-DD
            The current time (str): hh:mm:ss
        """
        now = datetime.datetime.now()
        d = u"{:4}-{:02}-{:02}".format(now.year, now.month, now.day)

        if millisecond is False:
            t = u"{:02}:{:02}:{:02}".format(now.hour, now.minute, now.second)
        else:
            t = u"{:02}:{:02}:{:02}.{:03}".format(now.hour, now.minute, now.second, now.microsecond)
        return d, t

    @staticmethod
    def get_file_created_date_and_time(path):
        """Get the date & time that a file was created

        Returns:
            The current date (str): YYYY-MM-DD
            The current time (str): hh:mm:ss
        """
        ct = os.path.getctime(path)
        ts = datetime.datetime.fromtimestamp(ct)
        d = u"{:4}-{:02}-{:02}".format(ts.year, ts.month, ts.day)
        t = u"{:02}:{:02}:{:02}".format(ts.hour, ts.minute, ts.second)
        return d, t

    @staticmethod
    def get_file_modified_date_and_time(path):
        """Get the date & time that a file was modified

        Returns:
            The current date (str): YYYY-MM-DD
            The current time (str): hh:mm:ss
        """
        mt = os.path.getmtime(path)
        ts = datetime.datetime.fromtimestamp(mt)
        d = u"{:4}-{:02}-{:02}".format(ts.year, ts.month, ts.day)
        t = u"{:02}:{:02}:{:02}".format(ts.hour, ts.minute, ts.second)
        return d, t

    @staticmethod
    def generate_str_with_time(base="output"):
        """Generate a string with the current time

        Args:
            base (str): The base file name

        Returns:
            A string created with the current time (str)
        """
        now = datetime.datetime.now()
        name = "({:4}-{:02}-{:02}_{:02}.{:02}.{:02})_{}".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second, base
        )
        return name

    @staticmethod
    def get_timezone():
        """Get the timezone setting

        Returns:
            Timezone (str): (UTC OO) Timezone
        """
        local_tz = dateutil.tz.tzlocal()
        local_offset = local_tz.utcoffset(datetime.datetime.now(local_tz))
        offset = local_offset.total_seconds() / 3600
        offset = int(offset) if offset == int(offset) else offset
        # name = local_tz.tzname(datetime.datetime.now(local_tz))
        # timezone = u"(UTC{}) {}".format(offset, name)
        if offset >= 0:
            timezone = u"UTC+{}".format(offset)
        else:
            timezone = u"UTC{}".format(offset)
        return timezone

    @staticmethod
    def save_bytes_to_file(path, data):
        """Save bytes to a file

        Args:
            path (str): The output path
            data (bytes): The data to be saved
        """
        try:
            f = open(path, "wb")
            f.write(data)
            f.close()
        except:
            pass

    @staticmethod
    def save_string_to_file(path, data):
        """Save string to a file

        Args:
            path (str): The output path
            data (str): The data to be saved
        """
        if len(path) > 256:
            name, ext = os.path.splitext(path)
            name = name[:240]
            path = name + ext

        try:
            f = open(path, "w", encoding="utf-8")
            f.write(data)
            f.close()
        except:
            pass

    @staticmethod
    def copy_file(src, dst):
        """Copy the src to the dest

        Args:
            src (str): The source path
            dst (str): The destination path
        """
        try:
            shutil.copy(src, dst)
        except:
            pass

    @staticmethod
    def delete_file(path):
        """Delete a file

        Args:
            path (str): The target path
        """
        try:
            path = os.path.abspath(path)
            # path = path.replace('[', '[[]').replace(']', '[]]')
            files = glob.glob(path)
            for f in files:
                os.remove(f)
        except:
            pass

    @staticmethod
    def delete_dir(path):
        """Delete a directory

        Args:
            path (str): The target path
        """
        try:
            shutil.rmtree(path, ignore_errors=True)
        except:
            pass

    @staticmethod
    def make_dir(path):
        """Make directories

        Args:
            path (str): The target path
        """
        try:
            path = os.path.abspath(path)
            os.makedirs(path, exist_ok=True)
            if os.path.isdir(path) is True:
                return True
        except:
            pass
        return False

    @staticmethod
    def run_command(cmd):
        """Run a command line

        Args:
            cmd (list): A command with arguments

        Returns:
            True or False
        """
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        ret = process.poll()
        return ret

    @staticmethod
    def hash_sha1(data, filemode=False):
        """Calculate SHA1 hash value

        Args:
            data (bytes)
            filemode (bool)

        Returns:
            SHA1 hash value
        """
        hash_context = hashlib.sha1()
        if filemode is False:
            hash_context.update(data)
        else:
            with open(data, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_context.update(chunk)
        return hash_context.hexdigest()

    @staticmethod
    def hash_sha256(data, filemode=False):
        """Calculate SHA256 hash value

        Args:
            data (bytes)
            filemode (bool)

        Returns:
            SHA256 hash value
        """
        hash_context = hashlib.sha256()
        if filemode is False:
            hash_context.update(data)
        else:
            with open(data, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_context.update(chunk)
        return hash_context.hexdigest()

    @staticmethod
    def get_valid_filename(s):
        """Get a valid filename

        Args:
            s (str): The filename

        Returns:
            A valid filename (str)
        """
        s = re.sub(r'[\\/*?:"<>|]', "_", s)
        return s

    @staticmethod
    def convert_unix_millisecond_to_str(value):
        """Convert a unix millisecond to string (local time)

        Args:
            value (int): Unix millisecond time

        Returns:
            The converted date (str): YYYY-MM-DD
            The converted time (str): hh:mm:ss
        """
        ts = datetime.datetime.fromtimestamp(int(value/1000))
        d = u"{:4}-{:02}-{:02}".format(ts.year, ts.month, ts.day)
        t = u"{:02}:{:02}:{:02}.{:03}".format(ts.hour, ts.minute, ts.second, int(value%1000))
        return d, t

    @staticmethod
    def convert_iso8602_to_str(value, millisecond=True):
        """Convert a iso8602 to string (local time)

        Args:
            value (string): iso8601
            millisecond (bool): If True, the return value contains millisecond

        Returns:
            The converted date (str): YYYY-MM-DD
            The converted time (str): hh:mm:ss
        """
        ts = iso8601.parse_date(value)
        ts = ts.replace(tzinfo=timezone.utc).astimezone(tz=None)
        d = u"{:4}-{:02}-{:02}".format(ts.year, ts.month, ts.day)

        if millisecond is True:
            t = u"{:02}:{:02}:{:02}.{:03}".format(ts.hour, ts.minute, ts.second, int(ts.microsecond/1000))
        else:
            t = u"{:02}:{:02}:{:02}".format(ts.hour, ts.minute, ts.second)
        return d, t

    @staticmethod
    def make_iso8602(d, t, millisecond=True):
        """Make a iso8602 using date and time strings

        Args:
            d (str): The converted date (YYYY-MM-DD)
            t (str): The converted time (hh:mm:ss.sss)
            millisecond (bool): If True, the return value contains millisecond

        Returns:
            iso8602 (str)
        """
        if millisecond is True:
            date = datetime.datetime.strptime(d + t, "%Y-%m-%d%H:%M:%S.%f")
            # iso8602 = date.isoformat()
        else:
            date = datetime.datetime.strptime(d + t, "%Y-%m-%d%H:%M:%S")

        local_tz = dateutil.tz.tzlocal()
        local_offset = local_tz.utcoffset(date)
        offset = local_offset.total_seconds() / 3600
        offset = int(offset) if offset == int(offset) else offset
        if offset >= 0:
            timezone = u"+{:02}00".format(offset)
        else:
            timezone = u"-{:02}00".format(abs(offset))

        iso8601 = "{}T{}{}".format(d, t, timezone)
        return iso8601

    @staticmethod
    def read_json(data):
        """Read json data

        Args:
            data (str)

        Returns:
            data (json)
        """
        try:
            data = json.loads(data)
        except ValueError:
            return None

        return data

    @staticmethod
    def macb(m, a, c, b):
        """Make 'MACB' mark

        Args:
            m (int): Modified
            a (int): Accessed
            c (int): Changed
            b (int): Birth

        Returns:
            'MACB' mark
        """
        if m == a == c == b:
            result = "MACB"

        return result

    @staticmethod
    def static_cast(buffer, structure):
        return cast(c_char_p(buffer), POINTER(structure)).contents

    @staticmethod
    def decompress_gzip(data):
        """Decompress gzip compressed data

        Args:
            data (bytes): Compressed data

        Returns:
            Decompressed data (bytes)
        """
        try:
            data = gzip.decompress(data)
        except:
            return b''
        return data

    @staticmethod
    def encode_url(u):
        """Build up a query string to go into a URL

        Returns:
            encoded (str)
        """
        return urllib.parse.quote_plus(u)

    @staticmethod
    def get_random():
        """Generate a random value

        Returns:
            A random value (float)
        """
        return random.random()

