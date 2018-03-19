"""pycift.utility.browser_automation

    * Description
        Browser automation module for pycift
"""

import sys
import time
import logging
import requests
from pycift.utility.pt_utils import PtUtils
from pycift.common_defines import *

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
logger.setLevel(logging.WARNING)
logger = logging.getLogger('urllib3.connectionpool')
logger.setLevel(logging.WARNING)
logger = logging.getLogger('requests.packages.urllib3.connectionpool')
logger.setLevel(logging.WARNING)

if sys.platform == "win32":
    import win32gui
else:
    logger = logging.getLogger('easyprocess')
    logger.setLevel(logging.WARNING)
    logger = logging.getLogger('pyvirtualdisplay')
    logger.setLevel(logging.WARNING)
    from pyvirtualdisplay import Display


class BrowserAutomation:

    def __init__(self, browser_driver):
        self.driver = browser_driver
        self.keys = Keys

        self.display = None
        self.browser = None

        self.id = ""
        self.pw = ""
        self.headers = {}
        self.cookies = {}
        self.login_success = False

        self.executable_path = ""

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

        if sys.platform == "win32":
            if self.driver is CIFTBrowserDrive.PHANTOMJS:
                self.executable_path = "C:\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe"
            elif self.driver is CIFTBrowserDrive.CHROME:
                self.executable_path = "chromedriver.exe"
        else:
            if self.driver is CIFTBrowserDrive.PHANTOMJS:
                self.executable_path = "phantomjs"
            elif self.driver is CIFTBrowserDrive.CHROME:
                self.executable_path = "chromedriver"

    def setup_driver(self, headers=None, default_directory="."):
        """Setup a browser driver

        Args:
            headers (dict): The custom headers
            default_directory (str): The default download directory
        """
        if sys.platform.startswith('linux'):
            self.create_virtual_display()

        if headers is None:
            headers = {}

        if not isinstance(headers, dict):
            self.prglog_mgr.info("{}(): 'headers' must be dict, so it will be ignored".format(GET_MY_NAME()))

        self.headers = headers

        if self.driver is CIFTBrowserDrive.PHANTOMJS:
            capabilities = webdriver.DesiredCapabilities.PHANTOMJS
            capabilities["phantomjs.page.settings.userAgent"] = (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"
            )
            capabilities["phantomjs.page.settings.cookiesEnabled"] = True
            # capabilities["phantomjs.page.settings.loadImages"] = False
            # capabilities["phantomjs.page.customHeaders.Accept"] = \
            #     "text/html,application/xhtml+xml,application/xml,application/vnd+amazon.uitoolkit+json,*/*"

            for key, value in headers.items():
                capabilities['phantomjs.page.customHeaders.{}'.format(key)] = value

            self.browser = webdriver.PhantomJS(
                executable_path=self.executable_path, desired_capabilities=capabilities
            )
        elif self.driver is CIFTBrowserDrive.CHROME:
            chrome_options = Options()
            chrome_options.add_argument("--lang=es")
            # chrome_options.add_argument('--start-maximized')
            # chrome_options.add_argument("--disable-extensions")
            # chrome_options.add_argument("--incognito")
            # chrome_options.add_argument("--silent-launch")
            #if default_directory != "":
            #    chrome_options.add_argument("download.default_directory={}".format(default_directory))
            chrome_options.add_experimental_option("prefs", {
                #'profile.default_content_settings': {'images': 2},
                "download.directory_upgrade": "true",
                "download.default_directory": default_directory,
                "download.prompt_for_download": False,
                "download.extensions_to_open": ""
            })

            if len(headers) > 0:
                extension_path = "chrome_header_modifier.zip"
                if self.create_modheaders_extension_for_chrome(
                    extension_path=extension_path,
                    add_or_modify_headers=headers
                ):
                    chrome_options.add_extension(extension_path)

            self.browser = webdriver.Chrome(
                executable_path=self.executable_path, chrome_options=chrome_options
            )

        self.browser.implicitly_wait(10)
        self.browser.set_page_load_timeout(10)
        self.browser.set_window_position(-5000, 0)

        # self.browser.set_window_position(0, 0)
        # self.browser.set_window_size(1920, 1280)
        # self.browser.set_window_size(0, 0)
        # self.browser.maximize_window()

    def create_virtual_display(self):
        """Create a virtual display

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # display = Display(visible=1, size=(1920, 1280))
        display = Display(visible=0, size=(1024, 768))
        display.start()

    def save_cookies(self, file_path):
        """Save cookies to a file

        Args:
            file_path (str): The path of cookie file
        """
        LINE = "document.cookie = '{name}={value}; path={path}; domain={domain}';\n"
        # LINE = "document.cookie = '{name}={value}; path={path}; domain={domain}; expiry={expiry}';\n"
        # LINE = "document.cookie = '{name}={value}; path={path}; domain={domain}; expires={expires}; expiry={expiry}; secure={secure}; httponly={httponly}';\n"
        with open(file_path, 'w', encoding='utf-8') as file:
            for cookie in self.browser.get_cookies():
                file.write(LINE.format(**cookie))

    def load_cookies(self, file_path):
        """Save cookies to a file

        Args:
            file_path (str): The path of cookie file
        """
        with open(file_path, 'r') as file:
            self.browser.execute_script(file.read())

        PtUtils.delete_file(file_path)

    def update_cookies(self):
        """Update the current cookie values

        """
        if self.browser is None:
            self.prglog_mgr.debug("{}(): Exception - a WebDriver should be created".format(GET_MY_NAME()))
        else:
            self.cookies = {}
            for item in self.browser.get_cookies():
                self.cookies[item["name"]] = item["value"]

    def visit(self, url):
        """Visit a URL

        Args:
            url (str): The URL address

        Returns:
            True or False
        """
        if self.browser is None:
            self.prglog_mgr.debug("{}(): Exception - a WebDriver should be created".format(GET_MY_NAME()))
            return False

        self.prglog_mgr.info("{}(): URL({})".format(GET_MY_NAME(), url))

        try:
            self.browser.get(url)
        except TimeoutException as e:
            self.prglog_mgr.debug("{}(): TimeoutException".format(GET_MY_NAME()))
            return False
        except Exception as e:
            self.prglog_mgr.debug("{}(): An exception occurred".format(GET_MY_NAME(), url))
            return False

        time.sleep(0.5)
        return True

    def get_bytes(self, url, cc):
        """Send a GET request to a URL

        Args:
            url (str): The URL address
            cc (dict): The customized cookies

        Returns:
            Bytes of returned messages (or None)
        """
        self.prglog_mgr.info("{}(): URL({})".format(GET_MY_NAME(), url))
        cookies = {}

        if cc is None and self.cookies != {}:
            cookies = self.cookies
        elif cc is None and self.browser is not None:
            for item in self.browser.get_cookies():
                cookies[item["name"]] = item["value"]
        else:
            cookies = cc

        try:
            r = requests.get(url, headers=self.headers, cookies=cookies, timeout=5)
        except Exception as e:
            self.prglog_mgr.debug("{}(): Exception({})".format(GET_MY_NAME(), e))
            return False

        if r.status_code != 200:
            self.prglog_mgr.debug("{}(): Status code {}({})".format(GET_MY_NAME(), r.status_code, r.reason))
            return None

        return r.content

    def get_text(self, url, cc=None):
        """Send a GET request to a URL

        Args:
            url (str): The URL address
            cc (dict): The customized cookies

        Returns:
            text of returned messages (or None)
        """
        self.prglog_mgr.info("{}(): URL({})".format(GET_MY_NAME(), url))
        cookies = {}

        if cc is None and self.cookies != {}:
            cookies = self.cookies
        elif cc is None and self.browser is not None:
            for item in self.browser.get_cookies():
                cookies[item["name"]] = item["value"]
                # self.prglog_mgr.debug("{}(): '{}' = '{}'".format(GET_MY_NAME(), item["name"], item["value"]))
        else:
            cookies = cc
            # for key, value in cc.items():
            #     cookies[key] = value

        try:
            r = requests.get(url, headers=self.headers, cookies=cookies, timeout=5)
        except Exception as e:
            self.prglog_mgr.debug("{}(): Exception({})".format(GET_MY_NAME(), e))
            return False

        if r.status_code != 200:
            self.prglog_mgr.debug("{}(): Status code {}({})".format(GET_MY_NAME(), r.status_code, r.reason))
            return None

        try:
            text = r.content.decode("utf-8")
        except UnicodeDecodeError:
            return r.text

        return text

    def save_as(self, url, outfile="a.out"):
        """Save as the current page

        Args:
            url (str): The URL address
            outfile (str): The output path

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): URL({})".format(GET_MY_NAME(), url))

        cookies = {}

        if self.browser is not None:
            for item in self.browser.get_cookies():
                cookies[item["name"]] = item["value"]
        else:
            cookies = self.cookies

        try:
            r = requests.get(url, cookies=cookies, timeout=5)
        except Exception as e:
            self.prglog_mgr.debug("{}(): Exception({})".format(GET_MY_NAME(), e))
            return False

        if r.status_code != 200:
            self.prglog_mgr.debug("{}(): Status code {}({})".format(GET_MY_NAME(), r.status_code, r.reason))
            return False

        with open(outfile, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True

    def close(self):
        """Post-process

        """
        if self.browser is not None:
            self.browser.quit()
            self.browser = None

    def create_modheaders_extension_for_chrome(self, extension_path, remove_headers=None, add_or_modify_headers=None):
        """Create 'modheaders' extension for Chrome

            Reference: https://vimmaniac.com/blog/bangal/modify-and-add-custom-headers-in-selenium-chrome-driver/

        Args:
            extension_path (str): The result extension path (ZIP compressed file)
            remove_headers (list): Headers names to remove
            add_or_modify_headers (dict): ie. {"Header Name": "Header Value"}

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): PATH({})".format(GET_MY_NAME(), extension_path))

        import string
        import zipfile

        if remove_headers is None:
            remove_headers = []

        if add_or_modify_headers is None:
            add_or_modify_headers = {}

        if not isinstance(remove_headers, list):
            self.prglog_mgr.debug("{}(): remove_headers must be a list".format(GET_MY_NAME()))
            return False

        if not isinstance(add_or_modify_headers, dict):
            self.prglog_mgr.debug("{}(): add_or_modify_headers must be dict".format(GET_MY_NAME()))
            return False

        # Only keeping the unique key in remove_headers list
        remove_headers = list(set(remove_headers))

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome HeaderModV",
            "permissions": [
                "webRequest",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = string.Template(
            """
            function callbackFn(details) {
                var remove_headers = ${remove_headers};
                var add_or_modify_headers = ${add_or_modify_headers};

                function inarray(arr, obj) {
                    return (arr.indexOf(obj) != -1);
                }

                // remove headers
                for (var i = 0; i < details.requestHeaders.length; ++i) {
                    if (inarray(remove_headers, details.requestHeaders[i].name)) {
                        details.requestHeaders.splice(i, 1);
                        var index = remove_headers.indexOf(5);
                        remove_headers.splice(index, 1);
                    }
                    if (!remove_headers.length) break;
                }

                // modify headers
                for (var i = 0; i < details.requestHeaders.length; ++i) {
                    if (add_or_modify_headers.hasOwnProperty(details.requestHeaders[i].name)) {
                        details.requestHeaders[i].value = add_or_modify_headers[details.requestHeaders[i].name];
                        delete add_or_modify_headers[details.requestHeaders[i].name];
                    }
                }

                // add modify
                for (var prop in add_or_modify_headers) {
                    details.requestHeaders.push(
                        {name: prop, value: add_or_modify_headers[prop]}
                    );
                }

                return {requestHeaders: details.requestHeaders};
            }

            chrome.webRequest.onBeforeSendHeaders.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking', 'requestHeaders']
            );
            """
        ).substitute(
            remove_headers=remove_headers,
            add_or_modify_headers=add_or_modify_headers,
        )

        with zipfile.ZipFile(extension_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        return True

