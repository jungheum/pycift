"""pycift.utility.binary_cookie

    * Description
        Binarycookie parser

        > This module was revised from source codes of an existing parser
          (http://securitylearn.net/wp-content/uploads/tools/iOS/BinaryCookieReader.py)
"""

import logging
from struct import unpack
from io import StringIO, BytesIO
from time import strftime, gmtime
from pycift.common_defines import *


class BinaryCookie:
    """BinaryCookie class

    Attributes:
        cookie_list (list): A list of cookie entries
        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self):
        self.cookie_list = []
        self.prglog_mgr = logging.getLogger(__name__)

    def parse(self, file_path):
        """Parse a binarycookie file

        Args:
            file_path (str): The full path of the target file
        """
        self.prglog_mgr.info("{}(): Parsing cache entries in \"{}\"".format(GET_MY_NAME(), file_path))

        try:
            file_object = open(file_path, 'rb')
        except IOError as exception:
            self.prglog_mgr.debug("{}(): Exception occurred".format(GET_MY_NAME()))
            return False

        file_header = file_object.read(4)  # Magic ('cook')
        if file_header != SIG_BINARYCOOKIE:
            self.prglog_mgr.debug("{}(): Not a Cookies.binarycookie file".format(GET_MY_NAME()))
            return False

        num_pages = unpack('>i', file_object.read(4))[0]  # Number of pages in the binary file: 4 bytes

        page_sizes = []
        for np in range(num_pages):
            page_sizes.append(unpack('>i', file_object.read(4))[0])  # Each page size: 4 bytes*number of pages

        pages = []
        for ps in page_sizes:
            pages.append(file_object.read(ps))  # Grab individual pages and each page will contain >= one cookie

        for page in pages:
            page = BytesIO(page)  # Converts the string to a file. So that we can use read/write operations easily.
            page.read(4)  # page header: 4 bytes: Always 00000100
            # Number of cookies in each page, first 4 bytes after the page header in every page.
            num_cookies = unpack('<i', page.read(4))[0]

            cookie_offsets = []
            for nc in range(num_cookies):
                # Every page contains >= one cookie. Fetch cookie starting point from page starting byte
                cookie_offsets.append(unpack('<i', page.read(4))[0])

            page.read(4)  # end of page header: Always 00000000

            cookie = ""
            domain = ""
            values = ""

            for offset in cookie_offsets:
                page.seek(offset)  # Move the page pointer to the cookie starting point
                cookiesize = unpack('<i', page.read(4))[0]  # fetch cookie size
                cookie = BytesIO(page.read(cookiesize))  # read the complete cookie

                cookie.read(4)  # unknown

                cookie_flags = ''
                flags = unpack('<i', cookie.read(4))[0]
                if flags == 0:
                    cookie_flags = ''
                elif flags == 1:
                    cookie_flags = 'Secure'
                elif flags == 4:
                    cookie_flags = 'HttpOnly'
                elif flags == 5:
                    cookie_flags = 'Secure | HttpOnly'
                else:
                    cookie_flags = 'Unknown'

                cookie.read(4)  # unknown

                urloffset = unpack('<i', cookie.read(4))[0]  # cookie domain offset from cookie starting point
                nameoffset = unpack('<i', cookie.read(4))[0]  # cookie name offset from cookie starting point
                pathoffset = unpack('<i', cookie.read(4))[0]  # cookie path offset from cookie starting point
                valueoffset = unpack('<i', cookie.read(4))[0]  # cookie value offset from cookie starting point

                endofcookie = cookie.read(8)  # end of cookie

                # Expiry date is in Mac epoch format: Starts from 1/Jan/2001
                expiry_date_epoch = unpack('<d', cookie.read(8))[0] + 978307200
                # 978307200 is unix epoch of  1/Jan/2001 //[:-1] strips the last space
                # expiry_date = strftime("%a, %d %b %Y ", gmtime(expiry_date_epoch))[:-1]
                expiry_date = strftime("%Y-%m-%d %H:%M:%S", gmtime(expiry_date_epoch))
                # Cookies creation time
                create_date_epoch = unpack('<d', cookie.read(8))[0] + 978307200
                # create_date = strftime("%a, %d %b %Y ", gmtime(create_date_epoch))[:-1]
                create_date = strftime("%Y-%m-%d %H:%M:%S", gmtime(create_date_epoch))

                cookie.seek(urloffset - 4)  # fetch domain value from url offset
                url = ''
                u = cookie.read(1)
                while unpack('<b', u)[0] != 0:
                    url = url + u.decode("utf-8")
                    u = cookie.read(1)

                cookie.seek(nameoffset - 4)  # fetch cookie name from name offset
                name = ''
                n = cookie.read(1)
                while unpack('<b', n)[0] != 0:
                    name = name + n.decode("utf-8")
                    n = cookie.read(1)

                cookie.seek(pathoffset - 4)  # fetch cookie path from path offset
                path = ''
                pa = cookie.read(1)
                while unpack('<b', pa)[0] != 0:
                    path = path + pa.decode("utf-8")
                    pa = cookie.read(1)

                cookie.seek(valueoffset - 4)  # fetch cookie value from value offset
                value = ''
                va = cookie.read(1)
                while unpack('<b', va)[0] != 0:
                    value = value + va.decode("utf-8")
                    va = cookie.read(1)

                domain = url
                values += "\"{}\": \"{}\",\n".format(name, value)

            self.cookie_list.append((domain, values[:-2]))

        file_object.close()
        return True

