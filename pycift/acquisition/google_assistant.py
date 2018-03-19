"""pycift.acquisition.google_assistant

    * Description
        pycift's acquisition Module for Google Assistant ecosystem
"""

import os
import time
import logging
import json

from pycift.common_defines import *
from pycift.utility.pt_utils import PtUtils
from pycift.utility.browser_automation import BrowserAutomation
from pycift.utility.binary_cookie import BinaryCookie
from pycift.report.db_models_google_assistant import *


# ===================================================================
# STRINGS
#
URL_PREFIX_GA_BASE  = "https://myactivity.google.com{}"
URL_PREFIX_GA_AUDIO = "https://myactivity.google.com/history/audio/play/{}"
URL_PREFIX_GA_AUDIO_RAW = "https://myactivity.google.com/history/audio/play/"


# # ===================================================================
# Enumerations
#
class CIFTGoogleAssistantAPI(Enum):
    """CIFTGoogleAssistantAPI class
    """
    UNKNOWN = (0x0000, "", "")

    ACTIVITIES \
        = (0x0010,
           "https://myactivity.google.com/item?hl=en-US&restrict=assist&jspb=1&ct={}",
           "Activity History")

    def __init__(self, code, url, desc):
        self._code = code
        self._url = url
        self._desc = desc

    @property
    def code(self):
        return self._code

    @property
    def url(self):
        return self._url

    @property
    def desc(self):
        return self._desc


class CIFTGoogleAssistantClientFile(Enum):
    """CIFTGoogleAssistantClientFile class
    """
    UNKNOWN = (0x0000, None, "", "")

    IOS_COOKIES \
        = (0x0001,
           SIG_BINARYCOOKIE,
           "/com.google.*/Library/Cookies/Cookies.binarycookies",
           "Binarycookies for Login Credential")

    def __init__(self, code, sig, path, desc):
        self._code = code
        self._sig = sig
        self._path = path
        self._desc = desc

    @property
    def code(self):
        return self._code

    @property
    def sig(self):
        return self._sig

    @property
    def path(self):
        return self._path

    @property
    def desc(self):
        return self._desc


# ===================================================================
# OPERATIONAL CLASSES
#
class GoogleAssistantInterface:
    """GoogleAssistantInterface class

    Attributes:
        path_base_dir (str): The directory path for storing result files
        browser_drive (CIFTBrowserDrive)
        inputs (list): The list of inputs
            [
                (CIFTOperation.CLOUD, ID1, Password1),
                (CIFTOperation.CLOUD, ID2, Password2),
                (CIFTOperation.CLOUD, cookies1),
                (CIFTOperation.CLOUD, cookies2),
                (CIFTOperation.COMPANION_APP_ANDROID, path_directory1),
                (CIFTOperation.COMPANION_APP_ANDROID, path_directory2),
                (CIFTOperation.COMPANION_WINDOWS_FILES, path_directory3),
                ...
            ]
        options (list): a set of CIFTOption

        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self):
        """The constructor
        """
        # class variables
        self.path_base_dir = ""
        self.browser_drive = None
        self.inputs = []
        self.options = []

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def basic_config(self, path_base_dir, browser_driver, options=[]):
        """Set the result DB path

        Args:
            path_base_dir (str): The directory path for storing result files
            browser_driver (CIFTBrowserDrive): A browser driver to automating web surfing
            options (list of CIFTOption): Set of detailed options

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Set the basic configurations".format(GET_MY_NAME()))

        if browser_driver not in CIFTBrowserDrive:
            self.prglog_mgr.debug("{}(): {} not in CIFTBrowserDrive".format(GET_MY_NAME(), browser_driver))
            return False

        self.browser_drive = browser_driver
        path_base_dir = os.path.abspath(path_base_dir)

        # if CIFT_DEBUG is False:
        #     if os.path.isdir(path_base_dir) is True:
        #         PtUtils.delete_dir(path_base_dir)

        if os.path.isdir(path_base_dir) is False:
            PtUtils.make_dir(path_base_dir)
            if os.path.isdir(path_base_dir) is False:
                return

        self.path_base_dir = path_base_dir
        self.prglog_mgr.info("{}(): Output path is {}".format(GET_MY_NAME(), path_base_dir))

        if len(options) != 0:
            for opt in options:
                if opt in CIFTOption:
                    self.options.append(opt)

        if len(self.options) != 0:
            self.prglog_mgr.info("{}(): Enabled options - {}".format(GET_MY_NAME(), self.options))
        return True

    def add_input(self, op, *args):
        """Set an input with an operation code and its arguments

        Args:
            op (CIFTOperation)
            args (list): Arguments

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Add a new input".format(GET_MY_NAME()))
        if op == CIFTOperation.CLOUD:
            self.prglog_mgr.info("{}(): OPERATION({}) ID({})".format(GET_MY_NAME(), op.name, args[0]))
        else:
            self.prglog_mgr.info("{}(): OPERATION({}) ARGS({})".format(GET_MY_NAME(), op.name, args))

        if op not in CIFTOperation:
            self.prglog_mgr.debug("{}(): {} not in CIFTOperation".format(GET_MY_NAME(), op))
            return False

        if len(args) == 0:
            self.prglog_mgr.debug(
                "{}(): At least one argument is required".format(GET_MY_NAME(), op)
            )
            return False

        item = (op,)
        for arg in args:
            item += (arg,)
        self.inputs.append(item)
        return True

    def run(self):
        """Process user inputs

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Run modules for processing user inputs".format(GET_MY_NAME()))

        if self.browser_drive is None or self.path_base_dir == "":
            self.prglog_mgr.debug("{}(): basic_config() should be called".format(GET_MY_NAME()))
            return False

        if len(self.inputs) == 0:
            self.prglog_mgr.debug("{}(): There is no input to be processed".format(GET_MY_NAME()))
            return False

        for item in self.inputs:
            op = item[0]

            if op is CIFTOperation.CLOUD:
                cloud = GoogleAssistantCloud(self.path_base_dir, self.browser_drive, self.options)
                if isinstance(item[1], dict):
                    cloud.run_with_cookie(item[1])
                    cloud.close()
                else:
                    cloud.run_with_idpw(item[1], item[2])
                    cloud.close()

            elif op is CIFTOperation.COMPANION_APP_ANDROID or \
                 op is CIFTOperation.COMPANION_APP_IOS or \
                 op is CIFTOperation.COMPANION_BROWSER_CHROME:
                companion = GoogleAssistantClient(self.path_base_dir)
                companion.run(op, item[1])
                companion.close()

            else:
                self.prglog_mgr.info("{}(): Not supported operation '{}'".format(GET_MY_NAME(), op.name))
                continue

        db_mgr = DatabaseManager("{}/{}".format(self.path_base_dir, RESULT_DB_GOOGLE_ASSISTANT), delete_db=False)
        db_mgr.dump_csv(self.path_base_dir)
        db_mgr.close()
        return True

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # Add post-processes
        return


class GoogleAssistantCloud:
    """GoogleAssistantCloud class

    Attributes:
        path_base_dir (str): The directory path for storing result files
        user_id (str): User ID for this cloud session
        user_pw (str): User Password for this cloud session
        options (list of CIFTOption): Set of detailed options

        auto (BrowserAutomation): The module for handling web-browsers
        parser (AmazonAlexaParser)

        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self, path_base_dir, browser_driver, options=[]):
        """The constructor

        Args:
            path_base_dir (str): The directory path for storing result files
            browser_driver (CIFTBrowserDrive): A browser driver to automating web surfing
            options (list of CIFTOption): Set of detailed options
        """
        self.parser = GoogleAssistantParser(path_base_dir)

        # class variables
        self.user_id = ""
        self.user_pw = ""
        self.options = options
        self.path_base_dir = "{}/{}/{}".format(path_base_dir, EVIDENCE_LIBRARY, __class__.__name__)
        PtUtils.make_dir(self.path_base_dir)

        if CIFT_DEBUG_CLOUD is True:
            self.auto = None
        else:
            self.auto = BrowserAutomation(browser_driver=browser_driver)

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def run_with_idpw(self, user_id, user_pw):
        """Get data from the cloud after connecting to its server using ID/PW

        Args:
            user_id (str): User ID
            user_pw (str): Password

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Get data from the cloud".format(GET_MY_NAME()))

        if user_id == "" or user_pw == "":
            self.prglog_mgr.debug("{}(): Invalid ID or PW".format(GET_MY_NAME()))
            return False
        else:
            self.prglog_mgr.info("{}(): ID({})".format(GET_MY_NAME(), user_id))

        # Set ID and PW
        self.user_id = user_id
        self.user_pw = user_pw

        if CIFT_DEBUG_CLOUD is False:
            # Set a driver
            self.auto.setup_driver(default_directory=self.path_base_dir)

            # Create a session with ID and PW
            if self.create_session() is False:
                self.prglog_mgr.debug("{}(): Creating a session failed".format(GET_MY_NAME()))
                return False

        try:
            # Call the internal APIs
            self.call_api()
        except Exception as e:
            self.prglog_mgr.debug("{}(): Exception from call_api() - ({})".format(GET_MY_NAME(), e))
            return False

        return True

    def run_with_cookie(self, cookies):
        """Get data from the cloud using cookies

            (1) The following values are required for Google authentication:
                'SID', 'SSID', 'HSID'

        Args:
            cookies (dict): at-main, sess-at-main, ubid-main, session-id and so on

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Get data from the cloud".format(GET_MY_NAME()))

        if cookies.get("SID") is None:
            self.prglog_mgr.debug("{}(): 'SID' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("SSID") is None:
            self.prglog_mgr.debug("{}(): 'SSID' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("HSID") is None:
            self.prglog_mgr.debug("{}(): 'HSID' is required".format(GET_MY_NAME()))
            return False

        self.prglog_mgr.info("{}(): Try to connect with cookies".format(GET_MY_NAME()))

        # Set headers and cookies
        self.auto.cookies = cookies

        # Test token values of cookies
        if self.test_credential() is False:
            self.prglog_mgr.debug("{}(): Invalid authentication tokens".format(GET_MY_NAME()))
            return False

        try:
            # Call the internal APIs
            self.call_api()
        except Exception as e:
            self.prglog_mgr.debug("{}(): Exception from call_api() - ({})".format(GET_MY_NAME(), e))
            return False

        return True

    def call_api(self):
        """Get data from the cloud by calling the internal APIs

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Get data from the cloud".format(GET_MY_NAME()))

        # -----------------------------------------------------------------------------
        # Call internal APIs for getting user data
        for api in CIFTGoogleAssistantAPI:

            # Set a default URL
            if api == CIFTGoogleAssistantAPI.ACTIVITIES:
                url = api.url.format("")
            else:
                url = api.url

            if url is "":
                continue

            while 1:
                if CIFT_DEBUG_CLOUD:
                    name = url
                    if len(name) > 128: name = name[:128]
                    name = PtUtils.get_valid_filename("{}.jspb".format(name))
                    path = "{}/{}".format(self.path_base_dir, name)

                    if os.path.exists(path):
                        # Load the previous result for debugging
                        data = open(path, encoding="utf-8").read()
                    else:
                        break
                else:
                    # Get the return (JSPB) of the API
                    data = self.auto.get_text(url)

                # Parse JSPB format and Save the result to DB
                if data is not None:
                    try:
                        self.parser.process_api(
                            CIFTOperation.CLOUD, api, url=url, value=data, filemode=False,
                            base_path=self.path_base_dir
                        )
                    except:
                        pass

                if api != CIFTGoogleAssistantAPI.ACTIVITIES:
                    break

                # Read JSPB format
                try:
                    data = json.loads(data[6:])
                except ValueError:
                    self.prglog_mgr.debug("{}(): Invalid JSPB format".format(GET_MY_NAME()))
                    return False

                if len(data) != 2:
                    break

                if data[0] is None:
                    break

                if api == CIFTGoogleAssistantAPI.ACTIVITIES:
                    # For getting more 'ACTIVITIES'
                    ct = data[1]
                    if ct is None:
                        break
                    self.prglog_mgr.info("{}(): \'ct\' is {}".format(GET_MY_NAME(), ct))
                    url = api.url.format(ct)
                continue

        # -----------------------------------------------------------------------------
        # Traverse all alexa devices registered at the cloud service
        if CIFTOption.DOWNLOAD_VOICE_DATA in self.options:
            self.download_voice_data()

        return True

    def download_voice_data(self):
        """Download voice data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Download voice data from Google Assistant cloud service".format(GET_MY_NAME()))

        query = (Timeline
                 .select(Timeline.date, Timeline.time, Timeline.timezone, Timeline.desc, Timeline.extra)
                 .where(Timeline.extra.contains(URL_PREFIX_GA_AUDIO_RAW))
                 .order_by(Timeline.date.desc(), Timeline.time.asc()))

        if len(query) == 0:
            self.prglog_mgr.debug("{}(): There is no Voice related URL".format(GET_MY_NAME()))
            return False

        path = "{}/VOICE/".format(self.path_base_dir)
        PtUtils.make_dir(path)

        voice_signature = "User\'s voice: "
        voice_url = ""

        for record in query:
            items = record.extra.split("|")
            for item in items:
                if item.startswith(voice_signature) is True:
                    voice_url = item.replace(voice_signature, "")
                    break

            # --------------------------------------------
            # Tokenize voice ID
            #
            voice_url = voice_url.replace("\"", "")
            voice_url = voice_url.replace(" ", "")
            voice_id = voice_url.replace(URL_PREFIX_GA_AUDIO_RAW, "")

            # Get a timestamp from voice ID
            d, t = PtUtils.convert_unix_millisecond_to_str(int(voice_id[:-3]))
            created_timestamp = PtUtils.make_iso8602(d, t)

            # Set a output file path
            desc = record.desc if len(record.desc) < 65 else record.desc[:63] + "..."
            if desc == "" or desc == "-":
                desc = "TRANSCRIPT NOT AVAILABLE"
            meta = "({})_TEXT({})".format(created_timestamp, desc)
            name = PtUtils.get_valid_filename(meta)
            path = "{}/VOICE/{}.mp3".format(self.path_base_dir, name)

            if CIFT_DEBUG_CLOUD is True:
                continue

            if os.path.exists(path) is True:
                self.prglog_mgr.info(
                    "{}(): Already downloaded file ({}) -> Go to the next file".format(GET_MY_NAME(), name)
                )
                continue

            # --------------------------------------------
            # Download a voice data to Evidence Library
            #
            if self.auto.save_as(voice_url, path) is False:
                continue

            if os.path.exists(path):
                self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path))
                data = open(path, 'rb').read()
            else:
                continue

            # --------------------------------------------
            # Insert a record into 'ACQUIRED_FILE' table
            #
            operation_id = -1
            query = Operation.select().where(Operation.type == CIFTOperation.CLOUD.name)
            if len(query) == 1:
                operation_id = query[0].id

            d, t = PtUtils.get_file_created_date_and_time(path)
            saved_timestamp = "{} {}".format(d, t)
            # d, t = PtUtils.get_file_modified_date_and_time(path)
            # modified_timestamp = "{} {}".format(d, t)

            AcquiredFile.create(
                operation_id=operation_id,
                src_path=voice_url,
                desc="Voice Data",
                saved_path=path,
                sha1=PtUtils.hash_sha1(data),
                saved_timestamp=saved_timestamp,
                modified_timestamp="-",
                timezone=PtUtils.get_timezone()
            )

        return True

    def create_session(self):
        """Create a session with ID and PW

        Returns:
            True and False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # url = "https://accounts.google.com/ServiceLogin"
        url = "https://www.google.com/accounts/Login?hl=en&continue=http://www.google.com/"
        if self.auto.visit(url) is False:
            return False

        # Set cookies
        tmp_name = PtUtils.generate_str_with_time("cookies.js")
        self.auto.save_cookies(tmp_name)
        self.auto.browser.delete_all_cookies()
        self.auto.load_cookies(tmp_name)

        # Try to login with ID and PW
        self.auto.browser.find_element_by_id("identifierId").send_keys(self.user_id)
        self.auto.browser.find_element_by_id("identifierNext").click()
        time.sleep(0.5)
        self.auto.browser.find_element_by_name("password").send_keys(self.user_pw)
        time.sleep(0.5)
        self.auto.browser.find_element_by_id("passwordNext").click()

        # self.auto.browser.save_screenshot('screenshot-1.png')
        # b64 = self.auto.browser.get_screenshot_as_base64()

        self.auto.browser.implicitly_wait(3)
        time.sleep(1)

        # self.auto.browser.save_screenshot('screenshot-2.png')
        # b64 = self.auto.browser.get_screenshot_as_base64()

        current_url = self.auto.browser.current_url
        title = self.auto.browser.title
        page_source = self.auto.browser.page_source
        # self.prglog_mgr.info("{}(): The current page's title is '{}'".format(GET_MY_NAME(), title))

        if page_source.find("Wrong password. Try again.") > 0:
            self.prglog_mgr.info("{}(): Login failed - Your password is incorrect".format(GET_MY_NAME()))
            return False

        if title != "Google":
            self.prglog_mgr.info("{}(): Login failed".format(GET_MY_NAME()))
            return False

        # Post-processes
        self.prglog_mgr.info("{}(): Logged in successfully".format(GET_MY_NAME()))
        self.auto.update_cookies()
        self.auto.close()
        return True

    def test_credential(self):
        """Test the current credential

        Returns:
            True and False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        text = self.auto.get_text(CIFTGoogleAssistantAPI.ACTIVITIES.url)
        if text is None:
            return False

        if not text.startswith(")]}'"):
            return False
        return True

    def close(self):
        """Post-process

        """
        if self.user_id != "":
            self.prglog_mgr.info("{}(): ID({})".format(GET_MY_NAME(), self.user_id))
        else:
            self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if self.auto is not None:
            self.auto.close()

        if self.parser is not None:
            self.parser.close()
        return


class GoogleAssistantParser:
    """GoogleAssistantParser class

    Attributes:
        path_base_dir (str): The directory path for storing result files
        db_mgr (DatabaseManager): The database module

        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self, path_base_dir, delete_db=True):
        """The constructor
        """
        # class variables
        self.path_base_dir = path_base_dir
        self.db_mgr = DatabaseManager(
            "{}/{}".format(path_base_dir, RESULT_DB_GOOGLE_ASSISTANT), delete_db
        )

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def process_api(self, op, api, url, value, filemode=True, base_path=""):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTGoogleAssistantAPI): The current Google Assistant API
            url (str): The URL related to this operation
            value (str): JSPB data itself or the path of JSPB file
            filemode (bool): If True, 'value' is the path of JSON file
            base_path (str): The base path for saving data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) API({})".format(GET_MY_NAME(), op.name, api.name))

        operation_id = -1
        source_id = -1

        if filemode is False:
            data = value
        else:
            path = value
            data = open(path, encoding="utf-8").read()

        # Read JSPB format
        if not data.startswith(")]}'"):
            self.prglog_mgr.debug("{}(): Invalid JSPB format".format(GET_MY_NAME()))
            return False

        try:
            data_temp = json.loads(data[6:])
        except ValueError:
            self.prglog_mgr.debug("{}(): Invalid JSPB format".format(GET_MY_NAME()))
            return False

        # --------------------------------------------
        # Save this data to Evidence Library
        name = "{} {}".format(url, PtUtils.get_random())
        name = PtUtils.hash_sha1(name.encode('utf-8'))
        path = "{}/{}.json".format(base_path, name)
        # name = PtUtils.get_valid_filename(url)
        # if len(name) > 128: name = name[:128]
        # # name = name.replace("https___", "")
        # path = "{}/{}.jspb".format(base_path, name)

        self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path))
        PtUtils.save_string_to_file(path, data)

        # --------------------------------------------
        # Insert a record into 'ACQUIRED_FILE' table
        #
        query = Operation.select().where(Operation.type == op.name)

        if len(query) == 1:
            operation_id = query[0].id

        d, t = PtUtils.get_file_created_date_and_time(path)
        saved_timestamp = "{} {}".format(d, t)
        d, t = PtUtils.get_file_modified_date_and_time(path)
        modified_timestamp = "{} {}".format(d, t)

        AcquiredFile.create(
            operation_id=operation_id,
            src_path=url,
            desc=api.desc,
            saved_path=path,
            sha1=PtUtils.hash_sha1(data.encode('utf-8')),
            saved_timestamp=saved_timestamp,
            modified_timestamp=modified_timestamp,
            timezone=PtUtils.get_timezone()
        )

        source_id = AcquiredFile.select().order_by(AcquiredFile.id.desc()).get()
        #
        # End of this segment
        # --------------------------------------------

        if api == CIFTGoogleAssistantAPI.UNKNOWN:
            self.prglog_mgr.info("{}(): UNSUPPORTED API - {}".format(GET_MY_NAME(), url))
            return True

        # Process JSPB data
        if data_temp[0] is None:
            self.prglog_mgr.info("{}(): There is no activity record in this JSPB file".format(GET_MY_NAME()))
            return True
        else:
            data = data_temp[0]

        if api == CIFTGoogleAssistantAPI.ACTIVITIES:
            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            query = AcquiredFile.select().where(AcquiredFile.id == source_id)
            if len(query) == 0:
                return False

            source = op.name
            source_type = query[0].desc
            filename = query[0].saved_path
            timezone = PtUtils.get_timezone()
            _format = "Android Web Cache + JSPB" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSPB"
            macb = "...B"
            _type = "Created"

            for act in data:  # processing each activity
                item_count = len(act)

                # Check the record type
                if 20 <= item_count <= 26:
                    self.prglog_mgr.info(
                        "{}(): Activity record detected - item_count({}) - Full".format(GET_MY_NAME(), item_count)
                    )
                    record = [None] * 26
                elif item_count == 10:
                    self.prglog_mgr.info(
                        "{}(): Activity record detected - item_count({}) - Simple".format(GET_MY_NAME(), item_count)
                    )
                    record = [None] * 10
                else:
                    self.prglog_mgr.info(
                        "{}(): Unknown activity record type - item_count({})".format(GET_MY_NAME(), item_count)
                    )
                    continue

                # Set a record
                idx = 0
                for item in act:
                    record[idx] = item
                    idx += 1

                # Get all three 'date and time'
                b_dt = PtUtils.convert_unix_millisecond_to_str(int(record[4][:-3]))

                short = 'History'

                desc = "-"
                if len(record) == 26:  # Full record
                    desc = record[9][0] if len(record[9]) > 2 else "-"

                notes = "-"
                if len(record) == 26 and record[13] is not None:  # Full record
                    idx = -1
                    if record[13][0][0] != "":
                        idx = 0
                    elif record[13][1][0] != "":
                        idx = 1
                    if idx != -1:
                        notes = "GA's answer: \"{}\"".format(''.join(record[13][idx][0]))
                elif len(record) == 26 and desc == "-":
                    notes = "TRANSCRIPT_NOT_AVAILABLE"
                elif len(record) == 10:  # Simple record
                    notes = "ACTIVATED"

                extra = ""
                if len(record) == 26:
                    if record[24] is not None:
                        extra = "User's voice: \"{}\"".format(''.join(record[24][0]))
                    if record[20] is not None:
                        if extra != "": extra += " | "
                        extra += "Location: \"{}\"".format(''.join(record[20][0][1]))
                    if record[19] is not None:
                        if extra != "": extra += " | "
                        extra += "Triggered by: \"{}\"".format(''.join(record[19][0]))

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                Timeline.create(
                    date=b_dt[0], time=b_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        return True

    def process_client_file(self, op, cf, value, filemode=True, base_path=""):
        """Process client files (SQLite DB, XML, binarycookies...) managed by companion applications

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTGoogleAssistantClientFile): The current Google Assistant app related file
            value (str): SQLite data itself or the path of a SQLite file
            filemode (bool): If True, 'value' is the file path
            base_path (str): The base path for saving data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) FILE({})".format(GET_MY_NAME(), op.name, cf.name))

        # Read data to buffer (if necessary)
        if filemode is False:
            data = value
        else:
            path = value
            if not os.path.exists(path):
                self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
                return False
            data = open(path, 'rb').read()

        # Set the file's extension
        if cf.sig == SIG_SQLITE:
            ext = 'db'
        elif cf.sig == SIG_BINARYCOOKIE:
            ext = 'binarycookies'
        elif cf.sig == SIG_XML:
            ext = 'xml'
        else:
            self.prglog_mgr.info("{}(): Not supported file format".format(GET_MY_NAME()))
            return False

        # --------------------------------------------
        # Save this data to Evidence Library
        name = "{} {}".format(cf.path, PtUtils.get_random())
        name = PtUtils.hash_sha1(name.encode('utf-8'))
        path = "{}/{}.{}".format(base_path, name, ext)
        # name = PtUtils.get_valid_filename(cf.path)
        # path = "{}/{}".format(base_path, name)

        self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path))
        PtUtils.save_bytes_to_file(path, data)

        # --------------------------------------------
        # Insert a record into 'ACQUIRED_DATA' table
        #
        query = Operation.select().where(Operation.type == op.name)

        if len(query) == 1:
            operation_id = query[0].id

        d, t = PtUtils.get_file_created_date_and_time(path)
        saved_timestamp = "{} {}".format(d, t)
        d, t = PtUtils.get_file_modified_date_and_time(path)
        modified_timestamp = "{} {}".format(d, t)

        AcquiredFile.create(
            operation_id=operation_id,
            src_path=cf.path,
            desc=cf.desc,
            saved_path=path,
            sha1=PtUtils.hash_sha1(data),
            saved_timestamp=saved_timestamp,
            modified_timestamp=modified_timestamp,
            timezone=PtUtils.get_timezone()
        )

        source_id = AcquiredFile.select().order_by(AcquiredFile.id.desc()).get()
        #
        # End of this segment
        # --------------------------------------------

        # Discriminate the name of this SQLite DB
        if cf == CIFTGoogleAssistantClientFile.UNKNOWN:
            return False

        # ---------------------------------------------------------
        if cf == CIFTGoogleAssistantClientFile.IOS_COOKIES:
            return self.process_client_file_ios_cookies(op, cf, source_id, path)

        return True

    def process_client_file_ios_cookies(self, op, cf, source_id, value, filemode=True):
        """Process iOS GA app's Cookies

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTGoogleAssistantClientFile): The current Google Assistant app related file
            source_id (int): The source ID for referencing an acquired file
            value (str): SQLite data itself or the path of a SQLite file
            filemode (bool): If True, 'value' is the file path

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) FILE({})".format(GET_MY_NAME(), op.name, cf.name))

        # Read data to buffer (if necessary)
        if filemode is True:
            path = value
        else:
            # Not yet
            return False

        bc = BinaryCookie()

        if bc.parse(path) is False:
            return False

        for domain, value in bc.cookie_list:
            if not domain.startswith(".google."):
                continue

            Credential.create(
                type="iOS Cookie",
                domain=domain,
                value=value,
                source_id=source_id
            )

        return True

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        self.db_mgr.close()
        return


class GoogleAssistantClient:
    """GoogleAssistantClient class

        - DBs, XMLs, Caches stored in storage devices
        - Credentials, DBs, XMLs, Caches remained in RAM dumps

    Attributes:
        path_base_dir (str): The directory path for storing result files
        parser (AmazonAlexaParser)

        prglog_mgr (logging): The progress log manager using the standard Python logging module
    """

    def __init__(self, path_base_dir):
        """The constructor
        """
        self.parser = GoogleAssistantParser(path_base_dir, delete_db=False)

        # class variables
        self.path_base_dir = "{}/{}/{}".format(path_base_dir, EVIDENCE_LIBRARY, __class__.__name__)
        PtUtils.make_dir(self.path_base_dir)

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def run(self, op, path):
        """Search and interpret Google Assistant related data stored within companion devices

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (directory or file)

        Returns:
            True or False
        """
        self.prglog_mgr.info(
            "{}(): Process Google Assistant related data stored within companion clients".format(GET_MY_NAME())
        )

        if not isinstance(op, CIFTOperation):
            self.prglog_mgr.debug("{}(): Invalid operation ({})".format(GET_MY_NAME(), op))
            return False

        if os.path.exists(path) is False:
            self.prglog_mgr.debug("{}(): Invalid path ({})".format(GET_MY_NAME(), path))
            return False
        else:
            self.prglog_mgr.info("{}(): OP({}) PATH({})".format(GET_MY_NAME(), op.name, path))

        ret = False

        if op is CIFTOperation.COMPANION_APP_IOS:
            ret = self.process_app_ios(op, path)

        return ret

    def process_app_ios(self, op, path):
        """Search and interpret Google Assistant related data stored within iOS devices

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (= the target directory)

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # --------------------------------
        # [Cookies.binarycookies]
        # ./Library/Cookies/Cookies.binarycookies
        self.parser.process_client_file(
            op, CIFTGoogleAssistantClientFile.IOS_COOKIES,
            path + "/Library/Cookies/Cookies.binarycookies",
            base_path=self.path_base_dir
        )

        return True

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if self.parser is not None:
            self.parser.close()
        return
