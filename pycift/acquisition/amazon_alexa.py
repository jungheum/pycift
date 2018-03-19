"""pycift.acquisition.amazon_alexa

    * Description
        pycift's acquisition Module for Amazon Alexa ecosystem
"""

import os
import time
import logging
import json
import re
from urllib.parse import urlparse, parse_qs

from pycift.common_defines import *
from pycift.utility.pt_utils import PtUtils
from pycift.utility.browser_automation import BrowserAutomation
from pycift.utility.chromium_main_cache import ChromiumMainCache, MainCacheEntry
from pycift.utility.chromium_simple_cache import ChromiumSimpleCache, SimpleCacheEntry
from pycift.utility.binary_cookie import BinaryCookie
from pycift.report.db_models_amazon_alexa import *


# ===================================================================
# STRINGS
#
HTTP_HEADER_ALEXA = {
        "Accept": "text/html,application/xhtml+xml,application/xml,application/vnd+amazon.uitoolkit+json,image/webp,image/apng,*/*"
        # 'application/vnd+amazon.uitoolkit+json' is required for 'skills-store.amazon.com' (important!!!)
    }
URL_PREFIX_ALEXA_BASE  = "https://alexa.amazon.com{}"
URL_PREFIX_ALEXA_AUDIO = "https://alexa.amazon.com/api/utterance/audio/data?id={}"
URL_PREFIX_ALEXA_AUDIO_RAW = "https://alexa.amazon.com/api/utterance/audio/data?id="
URL_PREFIX_ALEXA_CONVERSATION_AUDIO = "https://project-wink-mss-na.amazon.com/v1/media/{}"
URL_PREFIX_ALEXA_CONVERSATION_AUDIO_RAW = "https://project-wink-mss-na.amazon.com/v1/media/"


# # ===================================================================
# Enumerations
#
class CIFTAmazonAlexaAPI(Enum):
    """CIFTAmazonAlexaAPI class
    """
    UNKNOWN = (0x000000, "", "", "")

    BOOTSTRAP \
        = (0x000100,
           "https://alexa.amazon.com/api/bootstrap",
           "",
           "Bootstrap Account")

    HOUSEHOLD \
        = (0x000200,
           "https://alexa.amazon.com/api/household",
           "",
           "Household Accounts")

    SETTING_WIFI \
        = (0x000300,
           "https://alexa.amazon.com/api/wifi/configs",
           "",
           "WiFi Setting")

    SETTING_TRAFFIC \
        = (0x000400,
           "https://alexa.amazon.com/api/traffic/settings",
           "",
           "Traffic Setting")

    SETTING_CALENDAR \
        = (0x000500,
           "https://alexa.amazon.com/api/eon/householdaccounts",
           "",
           "Calendar Accounts")

    SETTING_WAKE_WORD \
        = (0x000600,
           "https://alexa.amazon.com/api/wake-word",
           "",
           "Wake Words")

    SETTING_BLUETOOTH \
        = (0x000700,
           "https://alexa.amazon.com/api/bluetooth",
           "",
           "Paired Bluetooth Devices")

    SETTING_THIRD_PARTY \
        = (0x000800,
           "https://alexa.amazon.com/api/third-party",
           "",
           "Third-Party Services")

    DEVICES \
        = (0x000901,  # deprecated
           "https://alexa.amazon.com/api/devices/device",
           "",
           "Registered Alexa Devices")

    DEVICES_V2 \
        = (0x000900,
           "https://alexa.amazon.com/api/devices-v2/device",
           "",
           "Registered Alexa Devices")

    DEVICE_PREFERENCES \
        = (0x000A00,
           "https://alexa.amazon.com/api/device-preferences",
           "",
           "Registered Alexa Devices' Preferences")

    COMPATIBLE_DEVICES \
        = (0x000B00,
           "https://alexa.amazon.com/api/phoenix",
           "",
           "Compatible Devices")

    TASK_LIST \
        = (0x000C01,  # deprecated
           "https://alexa.amazon.com/api/todos?type=TASK&size=1000",  # the current maximum size is 50?
           "",
           "To-do List")

    SHOPPING_LIST \
        = (0x000D01,  # deprecated
           "https://alexa.amazon.com/api/todos?type=SHOPPING_ITEM&size=1000",  # the current maximum size is 50?
           "",
           "Shopping List")

    NOTIFICATIONS \
        = (0x000E00,
           "https://alexa.amazon.com/api/notifications",
           "",
           "Timers & Alarms")

    CARDS \
        = (0x000F00,
           "https://alexa.amazon.com/api/cards?beforeCreationTime={}",
           "",
           "Home")

    ACTIVITIES \
        = (0x001000,  # the current maximum size is 50? It doesn't matter.
           "https://alexa.amazon.com/api/activities?startTime={}&size=1000&offset=-1",
           "https://alexa.amazon.com/api/activity-dialog-items?activityKey={}",
           "Activity History")

    ACTIVITY_DIALOG_ITEM \
        = (0x001101,  # this API depends on ACTIVITIES API
           "https://alexa.amazon.com/api/activity-dialog-items?activityKey={}",
           "",
           "Activity History")
    # (Example)
    # https://pitangui.amazon.com/api/activity-dialog-items?activityKey=A1TIJPBYY5HGTL%231508370435044%23A3F1S88NTZZXS9%23G030K51072126041&_=1509676703387

    MEDIA_HISTORY \
        = (0x001200,  # the current maximum size is 50? It doesn't matter.
           "https://alexa.amazon.com/api/media/historical-queue?deviceSerialNumber={}&deviceType={}&size=1000&offset=-1",
           "",
           "Played Media")

    SKILLS \
        = (0x001300,
           "https://skills-store.amazon.com/app/secure/yourskills",
           "",
           "Your Skills")

    NAMED_LIST \
        = (0x001400,
           "https://alexa.amazon.com/api/namedLists",
           "https://alexa.amazon.com/api/namedLists/{}/items",
           "Named List")

    COMMS_ACCOUNTS \
        = (0x001500,
           "https://alexa-comms-mobile-service.amazon.com/accounts",
           "",
           "Communication Account")

    COMMS_CONTACTS \
        = (0x001600,
           "https://alexa-comms-mobile-service.amazon.com/users/{}/contacts?view=full",
           "",
           "Contact List")

    COMMS_CONVERSATION \
        = (0x001700,
           "https://alexa-comms-mobile-service.amazon.com/users/{}/conversations",
           "https://alexa-comms-mobile-service.amazon.com/users/{}/conversations/{}/messages?sort=asc&startId=1",
           "Conversation List")

    # ----------------------------------------------
    CREDENTIAL_GOOGLE \
        = (0x001801,  # additional validation is required.
           "https://alexa.amazon.com/api/external-auth/link-url?provider=Ginger&service=Eon",
           "",
           "Linked Google Account")
    # (Example)
    # https://alexa.amazon.com/api/external-auth/link-url?provider=Google&service=Eon&_=1515559142515
    # 7eeaa670965a4693d7d0a5aa1a8a15ecba400764.json

    # ----------------------------------------------
    # [ Additional APIs found during research works ]
    #
    # https://pitangui.amazon.com/api/device-wifi-details?deviceSerialNumber=[REDACTED]&deviceType=A3S5BH2HU6VAYF&_=1509676703375
    # 3908e88281cd0e756fd1322db67c02aab8c0073f.json
    # {
    #     "deviceSerialNumber": "[REDACTED]",
    #     "deviceType": "A3S5BH2HU6VAYF",
    #     "essid": "SSID",
    #     "macAddress": "[REDACTED]"
    # }

    # https://alexa.amazon.com/api/speakers/id/amzn1.account.[REDACTED]?_=1515559142513
    # 9329bee5280738cca771623202a29a2d0733671b.json

    # https://skills-store.amazon.com/app/gateway?deviceType=app&pfm=ATVPDKIKX0DER&cor=US&lang=en-us&version=2&_=1515559142467
    # e801a323826b0ffbec2951bb01e05408494ebfe5.json
    # ----------------------------------------------

    def __init__(self, code, url, url_sub, desc):
        self._code = code
        self._url = url
        self._url_sub = url_sub
        self._desc = desc

    @property
    def code(self):
        return self._code

    @property
    def url(self):
        return self._url

    @property
    def url_sub(self):
        return self._url_sub

    @property
    def desc(self):
        return self._desc


class CIFTAmazonAlexaClientFile(Enum):
    """CIFTAmazonAlexaClientFile class
    """
    UNKNOWN = (0x0000, None, "", "")

    ANDROID_DATASTORE \
        = (0x0001,
           SIG_SQLITE,
           "/data/data/com.amazon.dee.app/databases/DataStore.db",
           "SQLite for To-do and Shopping List")

    ANDROID_MAP_DATA_STORAGE \
        = (0x0002,
           SIG_SQLITE,
           "/data/data/com.amazon.dee.app/databases/map_data_storage.db",
           "SQLite for Account and Device info.")

    ANDROID_MAP_DATA_STORAGE_V2 \
        = (0x0003,
           SIG_SQLITE,
           "/data/data/com.amazon.dee.app/databases/map_data_storage_v2.db",
           "SQLite for Account and Device info. (encrypted)")

    ANDROID_COOKIES \
        = (0x0004,
           SIG_SQLITE,
           "/data/data/com.amazon.dee.app/app_webview/Cookies",
           "SQLite for Login Credential")

    ANDROID_EVENTSFILE \
        = (0x0005,
           SIG_JSON,
           "/data/data/com.amazon.dee.app/app_901ad8be11e4424f875dc792db51f34d515d6767-01b7-49e5-8273-c8d11b0f331d\events\eventsFile",
           "Error Logs")

    IOS_LOCALDATA \
        = (0x0010,
           SIG_SQLITE,
           "/com.amazon.echo/Documents/LocalData.sqlite",
           "SQLite for To-do and Shopping List")

    IOS_COMMS \
        = (0x0011,
           SIG_SQLITE,
           "/com.amazon.echo/Documents/AlexaMobileiOSComms.sqlite",
           "SQLite for Messaging List")

    IOS_COOKIES \
        = (0x0012,
           SIG_BINARYCOOKIE,
           "/com.amazon.echo/Library/Cookies/Cookies.binarycookies",
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
class AmazonAlexaInterface:
    """AmazonAlexaInterface class

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
                cloud = AmazonAlexaCloud(self.path_base_dir, self.browser_drive, self.options)
                if isinstance(item[1], dict):
                    cloud.run_with_cookie(item[1])
                    cloud.close()
                else:
                    cloud.run_with_idpw(item[1], item[2])
                    cloud.close()

            elif op is CIFTOperation.COMPANION_APP_ANDROID or \
                 op is CIFTOperation.COMPANION_APP_IOS or \
                 op is CIFTOperation.COMPANION_BROWSER_CHROME:
                companion = AmazonAlexaClient(self.path_base_dir)
                companion.run(op, item[1])
                companion.close()

            else:
                self.prglog_mgr.info("{}(): Not supported operation '{}'".format(GET_MY_NAME(), op.name))
                continue

        db_mgr = DatabaseManager("{}/{}".format(self.path_base_dir, RESULT_DB_AMAZON_ALEXA), delete_db=False)
        db_mgr.dump_csv(self.path_base_dir)
        db_mgr.close()
        return True

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # Add post-processes
        return

        
class AmazonAlexaParser:
    """AmazonAlexaParser class

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
            "{}/{}".format(path_base_dir, RESULT_DB_AMAZON_ALEXA), delete_db
        )

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def process_api(self, op, api, url, value, filemode=True, base_path=""):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            value (str): JSON data itself or the path of JSON file
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
            data = open(path).read()

        # Read JSON format
        try:
            data_temp = json.loads(data)
        except ValueError:
            self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
            return False

        # --------------------------------------------
        # Save this data to Evidence Library
        name = "{} {}".format(url, PtUtils.get_random())
        name = PtUtils.hash_sha1(name.encode('utf-8'))
        path = "{}/{}.json".format(base_path, name)
        # name = PtUtils.get_valid_filename(url)
        # if len(name) > 128: name = name[:128]
        # name = name.replace("https___", "")
        # path = "{}/{}.json".format(base_path, name)

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
            modified_timestamp="-",
            timezone=PtUtils.get_timezone()
        )

        source_id = AcquiredFile.select().order_by(AcquiredFile.id.desc()).get()
        #
        # End of this segment
        # --------------------------------------------

        if api == CIFTAmazonAlexaAPI.UNKNOWN:
            self.prglog_mgr.info("{}(): UNSUPPORTED API - {}".format(GET_MY_NAME(), url))
            return True

        # Process JSON data
        data = data_temp

        if api == CIFTAmazonAlexaAPI.BOOTSTRAP:
            # --------------------------------------------
            # Insert a record into 'ACCOUNT' table
            #
            auth = data.get('authentication')
            if auth is not None:
                Account.create(
                    customer_email=auth.get('customerEmail'),
                    customer_name=auth.get('customerName'),
                    customer_id=auth.get('customerId'),
                    authenticated='True' if auth.get('authenticated') is True else 'False',
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.HOUSEHOLD:
            # --------------------------------------------
            # Insert a record into 'ACCOUNT' table
            #
            for account in data.get('accounts'):
                Account.create(
                    customer_email=account.get('email'),
                    customer_name=account.get('fullName'),
                    customer_id=account.get('id'),
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.COMMS_ACCOUNTS:
            # --------------------------------------------
            # Insert a record into 'ACCOUNT' table
            #
            for account in data:
                name = "{} {}".format(account.get('firstName'), account.get('lastName'))
                number = "+{}{}".format(account.get('phoneCountryCode'), account.get('phoneNumber'))

                Account.create(
                    customer_name=name,
                    phone_number=number,
                    comms_id=account.get('commsId'),
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.COMMS_CONTACTS:
            # --------------------------------------------
            # Insert a record into 'CONTACT' table
            #
            for entry in data:
                Contact.create(
                    first_name=entry.get("name").get("firstName"),
                    last_name=entry.get("name").get("lastName"),
                    number=entry.get("number"),
                    email=entry.get("emails"),
                    is_home_group='True' if entry.get('isHomeGroup') is True else 'False',
                    contact_id=entry.get("id"),
                    comms_id=entry.get("commsId")[0],
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_WIFI:
            # --------------------------------------------
            # Insert a record into 'SETTING_WIFI' table
            #
            for value in data.get('values'):
                SettingWifi.create(
                    ssid=value.get('ssid'),
                    security_method=value.get('securityMethod'),
                    pre_shared_key=value.get('preSharedKey'),
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_TRAFFIC:
            # --------------------------------------------
            # Insert a record into 'SETTING_MISC' table
            #
            origin = data.get('origin')
            if origin is not None:
                SettingMisc.create(
                    name='traffic_origin_address',
                    value=origin.get('label'),
                    source_id=source_id
                )

            for waypoint in data.get('waypoints'):
                SettingMisc.create(
                    name='traffic_waypoint',
                    value=waypoint.get('label'),
                    source_id=source_id
                )

            destination = data.get('destination')
            if origin is not None:
                SettingMisc.create(
                    name='traffic_destination_address',
                    value=destination.get('label'),
                    source_id=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_CALENDAR:
            # --------------------------------------------
            # Insert a record into 'SETTING_MISC' table
            #
            for account in data.get('householdAccountList'):
                if account.get('getCalendarAccountsResponse') is not None:
                    SettingMisc.create(
                        name='calendar_account',
                        value=account.get('getCalendarAccountsResponse'),
                        source_id=source_id
                    )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_WAKE_WORD:
            # --------------------------------------------
            # Insert a record into 'SETTING_MISC' table
            #
            for word in data.get('wakeWords'):
                if not isinstance(word, dict):
                    continue

                if word.get('wakeWord') is not None:
                    SettingMisc.create(
                        name='wake_word',
                        value=word.get('wakeWord'),
                        device_serial_number=word.get('deviceSerialNumber'),
                        source_id=source_id
                    )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_BLUETOOTH:
            # --------------------------------------------
            # Insert a record into 'SETTING_MISC' table
            #
            for bluetooth in data.get('bluetoothStates'):
                if bluetooth.get('pairedDeviceList') is not None:
                    SettingMisc.create(
                        name='paired_bluetooth_device',
                        value=bluetooth.get('pairedDeviceList'),
                        device_serial_number=bluetooth.get('deviceSerialNumber'),
                        source_id=source_id
                    )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.SETTING_THIRD_PARTY:
            # --------------------------------------------
            # Insert a record into 'SETTING_MISC' table
            #
            for service in data.get('services'):
                if service.get('serviceName') is not None:
                    SettingMisc.create(
                        name='third_party_service',
                        value=service.get('serviceName'),
                        source_id=source_id
                    )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.DEVICES or api == CIFTAmazonAlexaAPI.DEVICES_V2:
            # --------------------------------------------
            # Insert a record into 'ALEXA_DEVICE' table
            #
            for device in data.get('devices'):
                AlexaDevice.create(
                    device_account_name=device.get('accountName'),
                    device_family=device.get('deviceFamily'),
                    device_account_id=device.get('deviceAccountId'),
                    customer_id=device.get('deviceOwnerCustomerId'),
                    device_serial_number=device.get('serialNumber'),
                    device_type=device.get('deviceType'),
                    sw_version=device.get('softwareVersion'),
                    mac_address=device.get('macAddress'),
                    source=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.DEVICE_PREFERENCES:
            # --------------------------------------------
            # Insert a record into 'ALEXA_DEVICE' table
            #
            for df in data.get('devicePreferences'):
                AlexaDevice.create(
                    device_account_id=df.get('deviceAccountId'),
                    device_serial_number=df.get('deviceSerialNumber'),
                    device_type=df.get('deviceType'),
                    address=df.get('deviceAddress'),
                    postal_code=df.get('postalCode'),
                    locale=df.get('locale'),
                    search_customer_id=df.get('searchCustomerId'),
                    timezone=df.get('timeZoneId'),
                    region=df.get('timeZoneRegion'),
                    source=source_id
                )
            #
            # End of this segment
            # --------------------------------------------
            return True

        if api == CIFTAmazonAlexaAPI.COMPATIBLE_DEVICES:
            return self.process_api_phoenix(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.TASK_LIST or api == CIFTAmazonAlexaAPI.SHOPPING_LIST:
            return self.process_api_todos(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.NOTIFICATIONS:
            return self.process_api_notifications(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.CARDS:
            return self.process_api_cards(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.ACTIVITIES:
            return self.process_api_activities(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.MEDIA_HISTORY:
            return self.process_api_media_history(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.SKILLS:
            return self.process_api_skills(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.ACTIVITY_DIALOG_ITEM:
            return self.process_api_activity_dialog_items(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.NAMED_LIST:
            return self.process_api_namedlists(op, api, url, source_id, data)

        if api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION:
            return self.process_api_conversations(op, api, url, source_id, data)

        return True

    def process_api_phoenix(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))

        # --------------------------------------------
        # Insert a record into 'COMPATIBLE_DEVICE' table
        #
        if data.get('networkDetail') is not None:
            # PtUtils.save_string_to_file("temp.json", data.get('networkDetail'))
            try:
                temp = json.loads(data.get('networkDetail'))
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format ('networkDetail')".format(GET_MY_NAME()))
                return False
            else:
                # pprint.pprint(temp)
                data = temp

        try:
            root = (data.get('locationDetails').get('locationDetails')
                    .get('Default_Location').get('amazonBridgeDetails').get('amazonBridgeDetails'))
            if root is None:
                self.prglog_mgr.debug("{}(): Not found JSON path".format(GET_MY_NAME()))
                return False
        except:
            self.prglog_mgr.debug("{}(): Not found JSON path".format(GET_MY_NAME()))
            return False

        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"

        # Traverse all registered devices
        for key, value in root.items():
            if value.get('applianceDetails') is None or value.get('amazonBridgeIdentifier') is None:
                continue

            alexa_device_serial_number = value.get('amazonBridgeIdentifier').get('amazonBridgeDSN')
            alexa_device_type = value.get('amazonBridgeIdentifier').get('amazonBridgeType')

            apps = value.get('applianceDetails').get('applianceDetails')
            if apps is None:
                continue

            for name, app in apps.items():
                if name.find('uuid:') != 0:
                    # In this case, this app is not a physical device (just CLOUD_DISCOVERED_DEVICE?)-> skip
                    continue

                d, t = PtUtils.convert_unix_millisecond_to_str(app.get('applianceNetworkState').get('createdAt'))
                c_dt = "{} {}".format(d, t)

                # d, t = PtUtils.convert_unix_millisecond_to_str(app.get('applianceNetworkState').get('lastSeenAt'))
                # l_dt = "{} {}".format(d, t)

                d, t = PtUtils.convert_unix_millisecond_to_str(app.get('friendlyNameModifiedAt'))
                f_dt = "{} {}".format(d, t)

                # -------------------------
                # 'COMPATIBLE_DEVICE' table
                # -------------------------
                CompatibleDevice.create(
                    name=app.get('friendlyName'),
                    manufacture=app.get('manufacturerName'),
                    model=app.get('modelName'),
                    created=c_dt,
                    # last_seen=l_dt,
                    name_modified=f_dt,
                    desc=app.get('friendlyDescription'),
                    type=app.get('deviceType'),
                    reachable=app.get('reachable'),
                    firmware_version=app.get('firmwareVersion'),
                    appliance_id=app.get('applianceId'),
                    alexa_device_serial_number=alexa_device_serial_number,
                    alexa_device_type=alexa_device_type,
                    source=source_id
                )

                # -------------------------
                # 'TIMELINE' table
                # -------------------------
                # Get all three 'date and time'
                b = app.get('applianceNetworkState').get('createdAt')
                # m = app.get('applianceNetworkState').get('lastSeenAt')
                m = None  # 'lastSeenAt' has no meaning
                c = app.get('friendlyNameModifiedAt')

                short = app.get('friendlyName')

                desc = ""
                if app.get('friendlyDescription') is not None:
                    desc = app.get('friendlyDescription')

                if app.get('modelName') is not None:
                    desc += " | Model: \"{}\"".format(app.get('modelName'))

                if app.get('firmwareVersion') is not None:
                    desc += " | Firmware: \"{}\"".format(app.get('firmwareVersion'))

                if app.get('reachable') is True:
                    notes = "REACHABLE"
                else:
                    notes = "NOT_REACHABLE"

                if desc == "":
                    desc = "-"

                extra = "-"
                if app.get('applianceId') is not None:
                    extra = "Appliance ID: \"{}\"".format(app.get('applianceId'))

                # createdAt
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m == c:
                        macb = "M.CB"
                        _type = "Last Seen | Name Modified | Created"
                    elif b == m != c:
                        macb = "M..B"
                        _type = "Last Seen | Created"
                    elif b != m and b == c:
                        macb = "..CB"
                        _type = "Name Modified | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        host=alexa_device_serial_number,
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # lastSeenAt
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)

                    if m == c:
                        macb = "M.C."
                        _type = "Last Seen | Name Modified"
                    else:
                        macb = "M..."
                        _type = "Last Seen"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        host=alexa_device_serial_number,
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # friendlyNameModifiedAt
                if (c is not None) and ((b != c) and (m != c)):
                    c_dt = PtUtils.convert_unix_millisecond_to_str(c)

                    macb = "..C."
                    _type = "Name Modified"

                    Timeline.create(
                        date=c_dt[0], time=c_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        host=alexa_device_serial_number,
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

    def process_api_todos(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"

        if data.get('values') is None:
            if data.get('createdDate') is not None:
                data['values'] = [data]
            else:
                self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), api.name))
                return False

        for value in data.get('values'):
            # Get all three 'date and time'
            b = value.get('createdDate')
            m = value.get('lastUpdatedDate')
            c = value.get('lastLocalUpdatedDate')

            short = value.get('type')  # TASK or SHOPPING_ITEM
            desc = value.get('text')  # User's command

            notes = "-"
            if value.get('complete') is True and value.get('deleted') is True:
                notes = "COMPLETED | DELETED"
            elif value.get('complete') is True and value.get('deleted') is False:
                notes = "COMPLETED"
            elif value.get('complete') is False and value.get('deleted') is True:
                notes = "DELETED"

            extra = "-"
            if value.get('originalAudioId') is not None:
                extra = "User's voice: \"{}\"".format(URL_PREFIX_ALEXA_AUDIO.format(value.get('originalAudioId')))

            # createdDate
            if b is not None:
                b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                if b == m == c:
                    macb = "M.CB"
                    _type = "Last Updated | Last Local Updated | Created"
                elif b == m != c:
                    macb = "M..B"
                    _type = "Last Updated | Created"
                elif b != m and b == c:
                    macb = "..CB"
                    _type = "Last Local Updated | Created"
                else:
                    macb = "...B"
                    _type = "Created"

                Timeline.create(
                    date=b_dt[0], time=b_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    user=value.get('customerId'),  # host="",
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            # lastUpdatedDate
            if (m is not None) and (b != m):
                m_dt = PtUtils.convert_unix_millisecond_to_str(m)

                if m == c:
                    macb = "M.C."
                    _type = "Last Updated | Last Local Updated"
                else:
                    macb = "M..."
                    _type = "Last Updated"

                Timeline.create(
                    date=m_dt[0], time=m_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    user=value.get('customerId'),  # host="",
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            # lastLocalUpdatedDate
            if (c is not None) and ((b != c) and (m != c)):
                c_dt = PtUtils.convert_unix_millisecond_to_str(c)

                macb = "..C."
                _type = "Last Local Updated"

                Timeline.create(
                    date=c_dt[0], time=c_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    user=value.get('customerId'),  # host="",
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

    def process_api_notifications(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"
        macb = "...B"
        _type = "Created"

        if data.get('notifications') is None:
            if data.get('notification') is not None:
                data['notifications'] = [data]
            else:
                self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), api.name))
                return False

        for noti in data.get('notifications'):
            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(noti.get('createdDate'))

            short = noti.get('type')

            desc = "-"
            if noti.get('alarmTime') is not None:
                d, t = PtUtils.convert_unix_millisecond_to_str(noti.get('alarmTime'))
                desc = "{} {}".format(d, t)

            notes = noti.get('status')
            extra = "-"

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                host=noti.get('deviceSerialNumber'),
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

    def process_api_cards(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
        # --------------------------------------------
        # Insert a record into 'TIMELINE' table
        #
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        # filename = query[0].src_path
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"
        macb = "...B"
        _type = "Created"

        if data.get('cards') is None:
            if data.get('cardType') is not None:
                data['cards'] = [data]
            else:
                self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), api.name))
                return False

        for card in data.get('cards'):
            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(card.get('creationTimestamp'))

            short = card.get('cardType')
            desc = "-"
            if card.get('title') is not None:
                desc = "{}".format(card.get('title'))
                if card.get('subtitle') is not None and card.get('subtitle') is not "":
                    desc += " ({})".format(card.get('subtitle'))

            notes = ""
            extra = ""
            if card.get('playbackAudioAction') is not None:
                notes = card.get('playbackAudioAction').get('mainText')
                if card.get('playbackAudioAction').get('url') is not None:
                    extra = "User's voice: \"{}\"".format(
                        URL_PREFIX_ALEXA_BASE.format(card.get('playbackAudioAction').get('url'))
                    )

            if card.get('descriptiveText') is not None:
                if len(card.get('descriptiveText')) != 0:
                    if notes != "":
                        notes += " | "
                    notes += "Alexa's answer: \"{}\"".format(''.join(card.get('descriptiveText')))

            if card.get('cardType') == "EonCard":
                elist = card.get('eonEventList')
                if len(elist) > 0:
                    if extra != "":
                        extra += " | "
                    extra += "Event list: \"{}\"".format(elist)

            notes = notes.replace("\n", " ")
            extra = extra.replace("\n", " ")

            if notes == "": notes = "-"
            if extra == "": extra = "-"

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                user=card.get('registeredCustomerId'),
                host=card.get('sourceDevice').get('serialNumber'),
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

    def process_api_activities(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"
        macb = "...B"
        _type = "Created"

        if data.get('activities') is None:
            if data.get('activity') is not None:
                data['activities'] = [data.get('activity')]
            else:
                self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), api.name))
                return False

        for act in data.get('activities'):
            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(act.get('creationTimestamp'))

            short = 'History'

            desc = "-"
            if act.get('description') is not None:
                try:
                    temp = json.loads(act.get('description'))
                except ValueError:
                    pass
                else:
                    desc = "{}".format(temp.get('summary'))

            notes = "-"
            if act.get('activityStatus') is not None:
                notes = act.get('activityStatus')

            extra = "-"
            if act.get('utteranceId') is not None:
                extra = "User's voice: \"{}\"".format(
                    URL_PREFIX_ALEXA_AUDIO.format(act.get('utteranceId'))
                )

            notes = notes.replace("\n", " ")
            extra = extra.replace("\n", " ")
            if desc == "":
                desc = "-"

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                user=act.get('registeredCustomerId'),
                host=act.get('sourceDeviceIds')[0].get('serialNumber'),
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

    def process_api_activity_dialog_items(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"
        macb = "...B"
        _type = "Created"

        # if data.get('activities') is None:
        #     if data.get('activity') is not None:
        #         data['activities'] = [data.get('activity')]
        #     else:
        #         self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), api.name))
        #         return False

        for act in data.get('activityDialogItems'):
            if act.get('itemType') != "ASR" and act.get('itemType') != "TTS":
                continue

            # ASR: Automatic Speech Recognition (-> User's command)
            # NLU: Natural Language Understanding
            # TTS: Text-to-Speech (-> Alexa's answer)

            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(act.get('timestamp'))

            short = 'History (Dialog Items)'

            desc = "-"
            if act.get('activityItemData') is not None:
                try:
                    temp = json.loads(act.get('activityItemData'))
                except ValueError:
                    pass
                else:
                    if act.get('itemType') == "ASR":
                        desc = "{}".format(temp.get('asrText'))
                    else:
                        desc = "{}".format(temp.get('ttsText'))

            notes = "-"
            if act.get('itemType') == "ASR":
                notes = "User's command"
            else:
                notes = "Alexa's answer"
            # if act.get('activityStatus') is not None:
            #     notes = act.get('activityStatus')

            extra = "-"
            if act.get('itemType') == "ASR":
                if act.get('utteranceId') is not None:
                    extra = "User's voice: \"{}\"".format(
                        URL_PREFIX_ALEXA_AUDIO.format(act.get('utteranceId'))
                    )

            notes = notes.replace("\n", " ")
            extra = extra.replace("\n", " ")
            if desc == "":
                desc = "-"

            host = "-"
            try:
                temp = json.loads(act.get('sourceDevice'))
            except ValueError:
                pass
            else:
                host = "{}".format(temp.get('deviceSerialNumber'))

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                user=act.get('registeredUserId'),
                host=host,
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

    def process_api_media_history(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"
        macb = "...B"
        _type = "Started"

        o = parse_qs(urlparse(url).query, keep_blank_values=True)
        device_serial_number = o.get('deviceSerialNumber')[0]

        for m in data.get('media'):
            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(m.get('startTime'))

            short = m.get('contentType')

            desc = "-"
            if m.get('title') is not None:
                desc = "{}".format(m.get('title'))

            notes = "-"
            if m.get('providerId') is not None:
                notes = "Provider ID: \"{}\"".format(m.get('providerId'))

            extra = "-"
            if m.get('historicalId') is not None:
                extra = "Historical ID: \"{}\"".format(m.get('historicalId'))

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                host=device_serial_number,
                short=short if short != "" else "-",
                desc=desc if desc != "" else "-",
                notes=notes if notes != "" else "-",
                extra=extra if extra != "" else "-",
                filename=filename, format=_format,
            )

        for s in data.get('sessions'):
            # Get all three 'date and time'
            b_dt = PtUtils.convert_unix_millisecond_to_str(s.get('startTime'))

            short = s.get('contentType')

            desc = "-"
            if s.get('title') is not None:
                desc = "{}".format(s.get('title'))

            notes = "-"
            if s.get('providerId') is not None:
                notes = "Provider ID: \"{}\"".format(s.get('providerId'))

            extra = "-"
            if s.get('queueId') is not None:
                extra = "Queue ID: \"{}\"".format(s.get('queueId'))

            notes = notes.replace("\n", " ")
            extra = extra.replace("\n", " ")

            Timeline.create(
                date=b_dt[0], time=b_dt[1], timezone=timezone,
                MACB=macb, source=source, sourcetype=source_type, type=_type,
                host=device_serial_number,
                short=short if short != "" else "-",
                desc=desc if desc != "" else "-",
                notes=notes if notes != "" else "-",
                extra=extra if extra != "" else "-",
                filename=filename, format=_format,
            )

        # End of this segment
        # --------------------------------------------
        return True

    def process_api_skills(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))
        # --------------------------------------------
        # Insert a record into 'SKILL' table
        #
        if not isinstance(data, list):
            data = [data]

        for block in data:
            if not (block.get("block") == "data" and block.get("contents") is not None):
                continue

            contents = None
            for item in block.get("contents"):
                if item.get("id") == "skillsPageData":
                    contents = item.get("contents")
                    break

            if contents is None:
                continue

            for skill in contents:
                release_date = skill.get("productDetails").get("releaseDate")
                d, t = PtUtils.convert_unix_millisecond_to_str(int(release_date) * 1000)
                release_date = "{} {}".format(d, t)

                Skill.create(
                    title=skill.get("title"),
                    developer_name=skill.get("developerInfo").get("name"),
                    account_linked='True' if skill.get('entitlementInfo').get("accountLinked") is True else 'False',
                    release_date=release_date,
                    short=skill.get("shortDescription"),
                    desc=skill.get("productDetails").get("description"),
                    vendor_id=skill.get("productDetails").get("vendorId"),
                    skill_id=skill.get("productMetadata").get("skillId"),
                    source=source_id
                )
        #
        # End of this segment
        # --------------------------------------------
        return True

    def process_api_namedlists(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))

        # Discriminate the API type (main or sub)
        items = False
        if re.match('https://(alexa|pitangui).amazon.com/api/namedLists/[A-Za-z0-9=\-,]+/items', url):
            items = True

        # https://pitangui.amazon.com/api/namedLists?_=1509676703358
        # https://pitangui.amazon.com/api/namedLists/YW16bjEuYWNjb3VudC5BR1JMQ0hYNjRVTkNJQk9UTDRaQ0QzV0REWlhBLVNIT1BQSU5HX0lURU0=,YW16bjEuYWNjb3VudC5BRjNPVlpQQjZKVFZYNjJYTTdPWlU2S0hKSjNBLVNIT1BQSU5HX0lURU0=/items?startTime=&endTime=&completed=&listIds=YW16bjEuYWNjb3VudC5BR1JMQ0hYNjRVTkNJQk9UTDRaQ0QzV0REWlhBLVNIT1BQSU5HX0lURU0%3D%2CYW16bjEuYWNjb3VudC5BRjNPVlpQQjZKVFZYNjJYTTdPWlU2S0hKSjNBLVNIT1BQSU5HX0lURU0%3D&_=1509676703359

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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"

        if items is False:
            # https://alexa.amazon.com/api/namedLists => Named lists
            for namedlist in data.get('lists'):
                # Get timestamps
                b = namedlist.get('createdDate')
                m = namedlist.get('updatedDate')

                short = "-"
                if namedlist.get('type') is not None:
                    short = "Pre-defined list"
                elif namedlist.get('name') is not None:
                    short = "Customized list"

                desc = "-"
                if namedlist.get('type') is not None:
                    desc = namedlist.get('type')  # TO_DO or SHOPPING_LIST
                elif namedlist.get('name') is not None:
                    desc = namedlist.get('name')  # name of this list (custom list only)

                notes = "-"

                extra = "-"
                if namedlist.get('itemId') is not None:
                    extra = "itemId: \"{}\"".format(namedlist.get('itemId'))

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDate
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDate
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

        else:
            # https://alexa.amazon.com/api/namedLists/{}/items... => Entries of a named list
            for namedlist in data.get('list'):
                # Get timestamps
                b = namedlist.get('createdDateTime')
                m = namedlist.get('updatedDateTime')

                short = "A list entry"
                desc = namedlist.get('value')

                notes = "-"
                if namedlist.get('completed') is True:
                    notes = "COMPLETED"

                extra = "-"
                if namedlist.get('listId') is not None:
                    extra = "listId: \"{}\"".format(namedlist.get('listId'))

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDateTime
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDateTime
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
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

    def process_api_conversations(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))

        # Discriminate the API type (main or sub)
        messages = False
        if re.match('https://alexa-comms-mobile-service.amazon.com/users/[A-Za-z0-9~.]+/conversations/[A-Za-z0-9~.\-_]+/messages', url):
            messages = True

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
        _format = "Chromium Simple Cache + JSON" if op == CIFTOperation.COMPANION_APP_ANDROID else "JSON"

        if messages is False:
            # https://alexa-comms-mobile-service.amazon.com/users/{commsId}/conversations
            for entry in data.get('conversations'):
                macb = "M..."
                _type = "Updated"
                dt = PtUtils.convert_iso8602_to_str(entry.get('lastModified'))

                short = "Conversation"
                desc = "ConversationId: {}".format(entry.get('conversationId'))
                notes = "Participants: {}".format(entry.get('participants'))
                extra = "LastMessageId: {} | LastSequenceId: {}".format(
                    entry.get('lastMessageId'), entry.get('lastSequenceId')
                )

                Timeline.create(
                    date=dt[0], time=dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

        else:
            # https://alexa-comms-mobile-service.amazon.com/users/{}/conversations/{}/messages?sort=asc&startId=1
            for entry in data.get('messages'):
                macb = "...B"
                _type = "Created"
                dt = PtUtils.convert_iso8602_to_str(entry.get('time'))

                short = entry.get("type")

                desc = "-"
                if entry.get("type") == "message/text":
                    if entry.get("payload").get("text") is not None:
                        desc = entry.get("payload").get("text")
                elif entry.get("type") == "message/audio":
                    if entry.get("payload").get("transcript") is not None:
                        desc = entry.get("payload").get("transcript")

                notes = "MessageId: {} | Sender: {}".format(entry.get('messageId'), entry.get('sender'))

                extra = "-"
                if entry.get("type") == "message/audio":
                    if entry.get("payload").get("mediaId") is not None:
                        extra = "User's voice: \"{}\"".format(
                            URL_PREFIX_ALEXA_CONVERSATION_AUDIO.format(entry.get("payload").get("mediaId"))
                        )

                Timeline.create(
                    date=dt[0], time=dt[1], timezone=timezone,
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

    def process_api_template(self, op, api, url, source_id, data):
        """Process the cloud native data acquired by APIs or saved within companion devices

        Args:
            op (CIFTOperation): The current operation
            api (CIFTAmazonAlexaAPI): The current Amazon Alexa API
            url (str): The URL related to this operation
            source_id (int): The source ID for referencing an acquired file
            data (str): JSON data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({})".format(GET_MY_NAME(), op.name))

    def process_client_file(self, op, cf, value, filemode=True, base_path=""):
        """Process client files (SQLite DB, XML, binarycookies...) managed by companion applications

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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
            # self.prglog_mgr.info("{}(): Not supported file format".format(GET_MY_NAME()))
            # return False
            ext = ""

        # --------------------------------------------
        # Save this data to Evidence Library
        name = "{} {}".format(cf.path, PtUtils.get_random())
        name = PtUtils.hash_sha1(name.encode('utf-8'))
        if ext != "":
            path = "{}/{}.{}".format(base_path, name, ext)
        else:
            path = "{}/{}".format(base_path, name)
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
        # d, t = PtUtils.get_file_modified_date_and_time(path)
        # modified_timestamp = "{} {}".format(d, t)

        AcquiredFile.create(
            operation_id=operation_id,
            src_path=cf.path,
            desc=cf.desc,
            saved_path=path,
            sha1=PtUtils.hash_sha1(data),
            saved_timestamp=saved_timestamp,
            modified_timestamp="-",
            timezone=PtUtils.get_timezone()
        )

        source_id = AcquiredFile.select().order_by(AcquiredFile.id.desc()).get()
        #
        # End of this segment
        # --------------------------------------------

        # Discriminate the name of this SQLite DB
        if cf == CIFTAmazonAlexaClientFile.UNKNOWN:
            if cf.sig == SIG_SQLITE:
                cf = self.discriminate_sqlite_db(path)  # experimental
            else:
                return False

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_DATASTORE:
            return self.process_client_file_android_datastore(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE or \
           cf == CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE_V2:
            return self.process_client_file_android_map_data_storage(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_COOKIES:
            return self.process_client_file_android_cookies(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_EVENTSFILE:
            return self.process_client_file_android_eventsfile(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.IOS_LOCALDATA:
            return self.process_client_file_ios_localdata(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.IOS_COMMS:
            return self.process_client_file_ios_comms(op, cf, source_id, path)

        # ---------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.IOS_COOKIES:
            return self.process_client_file_ios_cookies(op, cf, source_id, path)

        return True

    def process_client_file_android_datastore(self, op, cf, source_id, value, filemode=True):
        """Process Android Alexa app's DataStore.db

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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

        # Open the saved SQLite DB
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False

        # Set common values
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "SQLite DB"

        # =======================================================================
        # Type 1 (old) ----------------------------------------------------------
        query = """
            Select * from DataItem
            where key = \"ToDoCollection.TASK\" or key = \"ToDoCollection.SHOPPING_ITEM\"
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            key = row.get('key')
            if key == "ToDoCollection.TASK" or key == "ToDoCollection.SHOPPING_ITEM":
                value = row.get('value')

                # Read JSON format
                try:
                    data = json.loads(value)
                except ValueError:
                    self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                    continue

                # --------------------------------------------
                # Insert a record into 'TIMELINE' table
                #
                if not isinstance(data, list):
                    if data.get('createdDate') is not None:
                        data = [data]
                    else:
                        self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), key))
                        return False

                for value in data:
                    # Get all three 'date and time'
                    b = value.get('createdDate')
                    m = value.get('lastUpdatedDate')
                    c = value.get('lastLocalUpdatedDate')

                    short = value.get('type')  # TASK or SHOPPING_ITEM
                    desc = value.get('text')  # User's command

                    notes = "-"
                    if value.get('complete') is True and value.get('deleted') is True:
                        notes = "COMPLETED | DELETED"
                    elif value.get('complete') is True and value.get('deleted') is False:
                        notes = "COMPLETED"
                    elif value.get('complete') is False and value.get('deleted') is True:
                        notes = "DELETED"

                    extra = "-"
                    if value.get('originalAudioId') is not None:
                        extra = "User's voice: \"{}\"".format(
                            URL_PREFIX_ALEXA_AUDIO.format(value.get('originalAudioId')))

                    # createdDate
                    if b is not None:
                        b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                        if b == m == c:
                            macb = "M.CB"
                            _type = "Last Updated | Last Local Updated | Created"
                        elif b == m != c:
                            macb = "M..B"
                            _type = "Last Updated | Created"
                        elif b != m and b == c:
                            macb = "..CB"
                            _type = "Last Local Updated | Created"
                        else:
                            macb = "...B"
                            _type = "Created"

                        Timeline.create(
                            date=b_dt[0], time=b_dt[1], timezone=timezone,
                            MACB=macb, source=source, sourcetype=source_type, type=_type,
                            user=value.get('customerId'),  # host="",
                            short=short if short != "" else "-",
                            desc=desc if desc != "" else "-",
                            notes=notes if notes != "" else "-",
                            extra=extra if extra != "" else "-",
                            filename=filename, format=_format,
                        )

                    # lastUpdatedDate
                    if (m is not None) and (b != m):
                        m_dt = PtUtils.convert_unix_millisecond_to_str(m)

                        if m == c:
                            macb = "M.C."
                            _type = "Last Updated | Last Local Updated"
                        else:
                            macb = "M..."
                            _type = "Last Updated"

                        Timeline.create(
                            date=m_dt[0], time=m_dt[1], timezone=timezone,
                            MACB=macb, source=source, sourcetype=source_type, type=_type,
                            user=value.get('customerId'),  # host="",
                            short=short if short != "" else "-",
                            desc=desc if desc != "" else "-",
                            notes=notes if notes != "" else "-",
                            extra=extra if extra != "" else "-",
                            filename=filename, format=_format,
                        )

                    # lastLocalUpdatedDate
                    if (c is not None) and ((b != c) and (m != c)):
                        c_dt = PtUtils.convert_unix_millisecond_to_str(c)

                        macb = "..C."
                        _type = "Last Local Updated"

                        Timeline.create(
                            date=c_dt[0], time=c_dt[1], timezone=timezone,
                            MACB=macb, source=source, sourcetype=source_type, type=_type,
                            user=value.get('customerId'),  # host="",
                            short=short if short != "" else "-",
                            desc=desc if desc != "" else "-",
                            notes=notes if notes != "" else "-",
                            extra=extra if extra != "" else "-",
                            filename=filename, format=_format,
                        )
                #
                # End of this segment
                # --------------------------------------------
                continue

        # =======================================================================
        # Type 2 (new) Named lists collection -----------------------------------
        itemIds = []

        query = """
            Select * from DataItem
            where key = \"NamedListsCollection\"
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            key = row.get('key')
            if key != "NamedListsCollection":
                continue

            value = row.get('value')

            # Read JSON format
            try:
                data = json.loads(value)
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                continue

            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            for namedlist in data:
                # Get timestamps
                b = namedlist.get('createdDate')
                m = namedlist.get('updatedDate')

                short = "-"
                if namedlist.get('type') is not None:
                    short = "Pre-defined list"
                elif namedlist.get('name') is not None:
                    short = "Customized list"

                desc = "-"
                if namedlist.get('type') is not None:
                    desc = namedlist.get('type')  # TO_DO or SHOPPING_LIST
                elif namedlist.get('name') is not None:
                    desc = namedlist.get('name')  # name of this list (custom list only)

                notes = "-"
                extra = "-"
                if namedlist.get('itemId') is not None:
                    extra = "itemId: \"{}\"".format(namedlist.get('itemId'))
                    itemIds.append((namedlist.get('itemId'), desc))  # for identifying a named list

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDate
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDate
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )
            #
            # End of this segment
            # --------------------------------------------
            continue

        query = """
            Select * from DataItem
            where key like \"NamedListItemsCollection.%\"
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            key = row.get('key')
            if not key.startswith("NamedListItemsCollection."):
                continue

            value = row.get('value')

            # Read JSON format
            try:
                data = json.loads(value)
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                continue

            list_name = ""
            for itemId, name in itemIds:
                if key.find(itemId) > 0:
                    list_name = name
                    break

            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            for namedlist in data:
                # Get timestamps
                b = namedlist.get('createdDateTime')
                m = namedlist.get('updatedDateTime')

                short = "A list entry"
                if list_name != "":
                    short = list_name

                desc = namedlist.get('value')

                notes = "-"
                if namedlist.get('completed') is True:
                    notes = "COMPLETED"

                extra = "-"
                if namedlist.get('listId') is not None:
                    extra = "listId: \"{}\"".format(namedlist.get('listId'))

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDateTime
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDateTime
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )
            #
            # End of this segment
            # --------------------------------------------
            continue

        return True

    def process_client_file_android_map_data_storage(self, op, cf, source_id, value, filemode=True):
        """Process Android Alexa app's map_data_storage.db

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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

        # Open the saved SQLite DB
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False

        # Set common values
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "SQLite DB"

        # Type 1 (old) ----------------------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE:
            query = """
                Select * from accounts;
            """
            rows = self.execute_sql(db, query)

            for record in rows:
                #
                # Insert a record into 'TIMELINE' table
                #
                macb = "M..."
                _type = "Last Updated"
                m_dt = PtUtils.convert_unix_millisecond_to_str(record.get('account_timestamp'))

                short = 'map_data_storage.accounts'
                desc = "-"
                if record.get('display_name') is not None:
                    desc = record.get('display_name')

                notes = "-"
                if record.get('account_deleted') is True and record.get('account_dirty') is True:
                    notes = "DELETED | DIRTY"
                elif record.get('account_deleted') is True and record.get('account_dirty') is False:
                    notes = "DELETED"
                elif record.get('account_deleted') is False and record.get('account_dirty') is True:
                    notes = "DIRTY"

                extra = "-"
                if record.get('directed_id') is not None:
                    extra = "Directed ID: \"{}\"".format(record.get('directed_id'))

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                Timeline.create(
                    date=m_dt[0], time=m_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    # user="", host="",
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            query = """
                Select * from device_data;
            """
            rows = self.execute_sql(db, query)

            for record in rows:
                #
                # Insert a record into 'TIMELINE' table
                #
                macb = "M..."
                _type = "Last Updated"
                m_dt = PtUtils.convert_unix_millisecond_to_str(record.get('device_data_timestamp'))

                short = 'map_data_storage.device_data'
                desc = "-"
                if record.get('device_data_namespace') is not None:
                    desc = "Namespace: {}".format(record.get('device_data_namespace'))

                notes = "-"
                if record.get('device_data_deleted') is True and record.get('device_data_dirty') is True:
                    notes = "DELETED | DIRTY"
                elif record.get('device_data_deleted') is True and record.get('device_data_dirty') is False:
                    notes = "DELETED"
                elif record.get('device_data_deleted') is False and record.get('device_data_dirty') is True:
                    notes = "DIRTY"

                extra = "{}: \"{}\"".format(
                    record.get('device_data_key'), record.get('device_data_value')
                )

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                Timeline.create(
                    date=m_dt[0], time=m_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    # user="", host="",
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            query = """
                Select * from tokens;
            """
            rows = self.execute_sql(db, query)

            for record in rows:
                #
                # Insert a record into 'TIMELINE' table
                #
                macb = "M..."
                _type = "Last Updated"
                m_dt = PtUtils.convert_unix_millisecond_to_str(record.get('token_timestamp'))

                short = 'map_data_storage.tokens'
                desc = "-"
                if record.get('token_account_id') is not None:
                    desc = "Account ID: {}".format(record.get('token_account_id'))

                notes = "-"
                if record.get('token_deleted') is True and record.get('token_dirty') is True:
                    notes = "DELETED | DIRTY"
                elif record.get('token_deleted') is True and record.get('token_dirty') is False:
                    notes = "DELETED"
                elif record.get('token_deleted') is False and record.get('token_dirty') is True:
                    notes = "DIRTY"

                extra = "{}: \"{}\"".format(
                    record.get('token_key'), record.get('token_value')
                )

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                Timeline.create(
                    date=m_dt[0], time=m_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            query = """
                Select * from userdata;
            """
            rows = self.execute_sql(db, query)

            for record in rows:
                #
                # Insert a record into 'TIMELINE' table
                #
                macb = "M..."
                _type = "Last Updated"
                m_dt = PtUtils.convert_unix_millisecond_to_str(record.get('userdata_timestamp'))

                short = 'map_data_storage.userdata'
                desc = "-"
                if record.get('userdata_account_id') is not None:
                    desc = "Account ID: {}".format(record.get('userdata_account_id'))

                notes = "-"
                if record.get('userdata_deleted') is True and record.get('userdata_dirty') is True:
                    notes = "DELETED | DIRTY"
                elif record.get('userdata_deleted') is True and record.get('userdata_dirty') is False:
                    notes = "DELETED"
                elif record.get('userdata_deleted') is False and record.get('userdata_dirty') is True:
                    notes = "DIRTY"

                extra = "{}: \"{}\"".format(
                    record.get('userdata_key'), record.get('userdata_value')
                )

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                Timeline.create(
                    date=m_dt[0], time=m_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

            return True

        # Type 2 (new) ----------------------------------------------------------------------
        if cf == CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE_V2:
            # Data decryption is required
            return True

    def process_client_file_android_cookies(self, op, cf, source_id, value, filemode=True):
        """Process Android Alexa app's Cookies

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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

        # Open the saved SQLite DB
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False

        # Set common values
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        # ----------------------------------------------------------------------
        query = """
            Select host_key, name, value from Cookies
        """
        rows = self.execute_sql(db, query)

        # cookies = []
        value = ""
        for row in rows:
            if not row.get('host_key').startswith(".amazon."):
                continue
            # d = dict()
            # d[row.get('name')] = row.get('value')
            # cookies.append(d)
            value += "\"{}\": \"{}\",\n".format(row.get('name'), row.get('value'))

        if value != "":
            Credential.create(
                type="Android Cookie",
                domain=".amazon.*",
                value=value[:-2],
                source_id=source_id
            )

        return True

    def process_client_file_android_eventsfile(self, op, cf, source_id, value, filemode=True):
        """Process Android Alexa app's eventsFile

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
            source_id (int): The source ID for referencing an acquired file
            value (str): Event data itself or the path of an event file
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
        _format = "JSON"
        macb = "...B"
        _type = "Created"

        with open(path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                # Read JSON format
                try:
                    data = json.loads(line)
                except ValueError:
                    self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                    continue

                # Get 'date and time'
                b_dt = PtUtils.convert_unix_millisecond_to_str(data.get('timestamp'))

                short = "Event Log"
                desc = data.get('event_type')
                notes = "{} {}".format(data.get('app_title'), data.get('app_version_name'))

                extra = ""
                if data.get('attributes') is not None:
                    extra += "EventType: \"{}\" | ".format(data.get('attributes').get('EventType'))
                    extra += "NetworkType: \"{}\"".format(data.get('attributes').get('NETWORK_TYPE'))

                notes = notes.replace("\n", " ")
                extra = extra.replace("\n", " ")

                if notes == "": notes = "-"
                if extra == "": extra = "-"

                Timeline.create(
                    date=b_dt[0], time=b_dt[1], timezone=timezone,
                    MACB=macb, source=source, sourcetype=source_type, type=_type,
                    short=short if short != "" else "-",
                    desc=desc if desc != "" else "-",
                    notes=notes if notes != "" else "-",
                    extra=extra if extra != "" else "-",
                    filename=filename, format=_format,
                )

        return True

    def process_client_file_ios_localdata(self, op, cf, source_id, value, filemode=True):
        """Process iOS Alexa app's LocalData.db

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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

        # Open the saved SQLite DB
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False

        # Set common values
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "SQLite DB"

        # =======================================================================
        # Type 1 (old) ----------------------------------------------------------
        query = """
            Select ZKEY, ZVALUE from ZDATAITEM
            where ZKEY = \"ToDoCollection.TASK\" or ZKEY = \"ToDoCollection.SHOPPING_ITEM\"
        """
        rows = self.execute_sql(db, query)

        for record in rows:
            key = record.get('ZKEY')
            value = record.get('ZVALUE')

            # Read JSON format
            try:
                data = json.loads(value)
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                continue

            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            if not isinstance(data, list):
                if data.get('createdDate') is not None:
                    data = [data]
                else:
                    self.prglog_mgr.debug("{}(): Invalid '{}'".format(GET_MY_NAME(), key))
                    return False

            for value in data:
                # Get all three 'date and time'
                b = value.get('createdDate')
                m = value.get('lastUpdatedDate')
                c = value.get('lastLocalUpdatedDate')

                short = value.get('type')  # TASK or SHOPPING_ITEM
                desc = value.get('text')  # User's command

                notes = "-"
                if value.get('complete') is True and value.get('deleted') is True:
                    notes = "COMPLETED | DELETED"
                elif value.get('complete') is True and value.get('deleted') is False:
                    notes = "COMPLETED"
                elif value.get('complete') is False and value.get('deleted') is True:
                    notes = "DELETED"

                extra = "-"
                if value.get('originalAudioId') is not None:
                    extra = "User's voice: \"{}\"".format(
                        URL_PREFIX_ALEXA_AUDIO.format(value.get('originalAudioId')))

                # createdDate
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m == c:
                        macb = "M.CB"
                        _type = "Last Updated | Last Local Updated | Created"
                    elif b == m != c:
                        macb = "M..B"
                        _type = "Last Updated | Created"
                    elif b != m and b == c:
                        macb = "..CB"
                        _type = "Last Local Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=value.get('customerId'),  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # lastUpdatedDate
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)

                    if m == c:
                        macb = "M.C."
                        _type = "Last Updated | Last Local Updated"
                    else:
                        macb = "M..."
                        _type = "Last Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=value.get('customerId'),  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # lastLocalUpdatedDate
                if (c is not None) and ((b != c) and (m != c)):
                    c_dt = PtUtils.convert_unix_millisecond_to_str(c)

                    macb = "..C."
                    _type = "Last Local Updated"

                    Timeline.create(
                        date=c_dt[0], time=c_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=value.get('customerId'),  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )
            #
            # End of this segment
            # --------------------------------------------
            continue

        # =======================================================================
        # Type 2 (new) Named lists collection -----------------------------------
        itemIds = []

        query = """
            Select ZKEY, ZVALUE from ZDATAITEM
            where ZKEY = \"NamedListsCollection\"
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            key = row.get('ZKEY')
            if key != "NamedListsCollection":
                continue

            value = row.get('ZVALUE')

            # Read JSON format
            try:
                data = json.loads(value)
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                continue

            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            for namedlist in data:
                # Get timestamps
                b = namedlist.get('createdDate')
                m = namedlist.get('updatedDate')

                short = "-"
                if namedlist.get('type') is not None:
                    short = "Pre-defined list"
                elif namedlist.get('name') is not None:
                    short = "Customized list"

                desc = "-"
                if namedlist.get('type') is not None:
                    desc = namedlist.get('type')  # TO_DO or SHOPPING_LIST
                elif namedlist.get('name') is not None:
                    desc = namedlist.get('name')  # name of this list (custom list only)

                notes = "-"
                extra = "-"
                if namedlist.get('itemId') is not None:
                    extra = "itemId: \"{}\"".format(namedlist.get('itemId'))
                    itemIds.append((namedlist.get('itemId'), desc))  # for identifying a named list

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDate
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDate
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )
            #
            # End of this segment
            # --------------------------------------------
            continue

        query = """
            Select ZKEY, ZVALUE from ZDATAITEM
            where ZKEY like \"NamedListItemsCollection.%\"
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            key = row.get('ZKEY')
            if not key.startswith("NamedListItemsCollection."):
                continue

            value = row.get('ZVALUE')

            # Read JSON format
            try:
                data = json.loads(value)
            except ValueError:
                self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                continue

            list_name = ""
            for itemId, name in itemIds:
                if key.find(itemId) > 0:
                    list_name = name
                    break

            # --------------------------------------------
            # Insert a record into 'TIMELINE' table
            #
            for namedlist in data:
                # Get timestamps
                b = namedlist.get('createdDateTime')
                m = namedlist.get('updatedDateTime')

                short = "A list entry"
                if list_name != "":
                    short = list_name

                desc = namedlist.get('value')

                notes = "-"
                if namedlist.get('completed') is True:
                    notes = "COMPLETED"

                extra = "-"
                if namedlist.get('listId') is not None:
                    extra = "listId: \"{}\"".format(namedlist.get('listId'))

                user = "-"
                if namedlist.get('customerId') is not None:
                    user = namedlist.get('customerId')

                # createdDateTime
                if b is not None:
                    b_dt = PtUtils.convert_unix_millisecond_to_str(b)

                    if b == m:
                        macb = "M..B"
                        _type = "Updated | Created"
                    else:
                        macb = "...B"
                        _type = "Created"

                    Timeline.create(
                        date=b_dt[0], time=b_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )

                # updatedDateTime
                if (m is not None) and (b != m):
                    m_dt = PtUtils.convert_unix_millisecond_to_str(m)
                    macb = "M..."
                    _type = "Updated"

                    Timeline.create(
                        date=m_dt[0], time=m_dt[1], timezone=timezone,
                        MACB=macb, source=source, sourcetype=source_type, type=_type,
                        user=user,  # host="",
                        short=short if short != "" else "-",
                        desc=desc if desc != "" else "-",
                        notes=notes if notes != "" else "-",
                        extra=extra if extra != "" else "-",
                        filename=filename, format=_format,
                    )
            #
            # End of this segment
            # --------------------------------------------
            continue

        return True

    def process_client_file_ios_comms(self, op, cf, source_id, value, filemode=True):
        """Process iOS Alexa app's AlexaMobileiOSComms.sqlite

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
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

        # Open the saved SQLite DB
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False

        # Set common values
        query = AcquiredFile.select().where(AcquiredFile.id == source_id)
        if len(query) == 0:
            return False

        source = op.name
        source_type = query[0].desc
        filename = query[0].saved_path
        timezone = PtUtils.get_timezone()
        _format = "SQLite DB"
        macb = "...B"
        _type = "Created"

        query = """
            Select * from ZMESSAGEENTITY
        """
        rows = self.execute_sql(db, query)

        for row in rows:
            b_dt = PtUtils.convert_iso8602_to_str(row.get('ZMESSAGETIME'))

            short = 'Message'
            desc = row.get("ZMESSAGEBODY")
            notes = row.get("ZMESSAGETYPE")

            extra = "-"
            if row.get('ZMEDIAURL') is not None:
                extra = "User's voice: \"{}\"".format(
                    URL_PREFIX_ALEXA_CONVERSATION_AUDIO.format(row.get('ZMEDIAURL'))
                )
            if row.get('ZLOCALURL') is not None and row.get('ZLOCALURL') != "":
                if extra != "":
                    extra += " | "
                extra += "Local file: \"{}\"".format(row.get('ZLOCALURL'))

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

        return True

    def process_client_file_ios_cookies(self, op, cf, source_id, value, filemode=True):
        """Process iOS Alexa app's Cookies.binarycookies

        Args:
            op (CIFTOperation): The current operation
            cf (CIFTAmazonAlexaClientFile): The current Amazon Alexa app related file
            source_id (int): The source ID for referencing an acquired file
            value (str): Binarycookie data itself or the path of a Binarycookie file
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
            if not domain.startswith(".amazon."):
                continue

            Credential.create(
                type="iOS Cookie",
                domain=domain,
                value=value,
                source_id=source_id
            )

        return True

    def discriminate_sqlite_db(self, path):
        """Discriminate the name of the SQLite DB (NOT USED)

        Args:
            path (str): The full path of the SQLite DB

        Returns:
            True or False
        """
        try:
            db = SqliteDatabase(path)
            tables = db.get_tables()
        except:
            self.prglog_mgr.debug("{}(): Invalid SQLite".format(GET_MY_NAME()))
            return False
        else:
            query = "Select * from DataItem"
            cursor = db.execute_sql(query)
            ncols = len(cursor.description)
            colnames = [cursor.description[i][0] for i in range(ncols)]

        sqlite = CIFTAmazonAlexaClientFile.UNKNOWN

        '''
        CIFTAmazonAlexaClientFile.ANDROID_DATASTORE
            CREATE TABLE android_metadata (locale TEXT);
            CREATE TABLE DataItem (key TEXT PRIMARY KEY,value TEXT );
        '''

        '''
        CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE
            CREATE TABLE accounts (_id INTEGER PRIMARY KEY AUTOINCREMENT, directed_id TEXT UNIQUE NOT NULL, display_name TEXT UNIQUE, account_timestamp INTEGER NOT NULL, account_deleted INTEGER NOT NULL, account_dirty INTEGER NOT NULL);
            CREATE TABLE android_metadata (locale TEXT);
            CREATE TABLE device_data (_id INTEGER PRIMARY KEY AUTOINCREMENT, device_data_namespace TEXT NOT NULL, device_data_key TEXT NOT NULL, device_data_value TEXT, device_data_timestamp INTEGER NOT NULL, device_data_deleted INTEGER NOT NULL, device_data_dirty INTEGER NOT NULL, UNIQUE(device_data_namespace,device_data_key));
            CREATE TABLE tokens (_id INTEGER PRIMARY KEY AUTOINCREMENT, token_account_id TEXT NOT NULL, token_key TEXT NOT NULL, token_value TEXT, token_timestamp INTEGER NOT NULL, token_deleted INTEGER NOT NULL, token_dirty INTEGER NOT NULL, UNIQUE(token_account_id,token_key));
            CREATE TABLE userdata (_id INTEGER PRIMARY KEY AUTOINCREMENT, userdata_account_id TEXT NOT NULL, userdata_key TEXT NOT NULL, userdata_value TEXT, userdata_timestamp INTEGER NOT NULL, userdata_deleted INTEGER NOT NULL, userdata_dirty INTEGER NOT NULL, UNIQUE(userdata_account_id,userdata_key));
        '''

        '''
        CIFTAmazonAlexaClientFile.IOS_LOCALDATA
            CREATE TABLE ZDATAITEM ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER, Z_OPT INTEGER, ZKEY VARCHAR, ZVALUE VARCHAR );
            CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID VARCHAR(255), Z_PLIST BLOB);
            CREATE TABLE Z_MODELCACHE (Z_CONTENT BLOB);
            CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER);
            CREATE INDEX ZDATAITEM_ZKEY_INDEX ON ZDATAITEM (ZKEY);
        '''
        return sqlite

    def execute_sql(self, db, query):
        """Execute a SQL query

        Args:
            db (str): The current database instance
            query (str): The query string

        Returns:
            Result (list of dict)
        """
        try:
            cursor = db.execute_sql(query)
        except Exception as e:
            self.prglog_mgr.debug("{}(): {}".format(GET_MY_NAME(), e))
            return []

        ncols = len(cursor.description)
        colnames = [cursor.description[i][0] for i in range(ncols)]

        rows = []
        for row in cursor.fetchall():
            res = {}
            for i in range(ncols):
                res[colnames[i]] = row[i]
            rows.append(res)

        return rows

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        self.db_mgr.close()
        return


class AmazonAlexaCloud:
    """AmazonAlexaCloud class

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
        self.parser = AmazonAlexaParser(path_base_dir)

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
            # Setup a driver
            self.auto.setup_driver(headers=HTTP_HEADER_ALEXA, default_directory=self.path_base_dir)

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

            (1) The following values are required for calling Alexa's internal APIs:
                'at-main', 'sess-at-main', 'ubid-main', 'session-id'

            (2) The 'x-main' value is required for calling Alexa's SKILL API

        Args:
            cookies (dict): at-main, sess-at-main, ubid-main, session-id and so on

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): Get data from the cloud".format(GET_MY_NAME()))

        if cookies.get("session-id") is None:
            self.prglog_mgr.debug("{}(): 'session-id' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("ubid-main") is None:
            self.prglog_mgr.debug("{}(): 'ubid-main' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("sess-at-main") is None:
            self.prglog_mgr.debug("{}(): 'sess-at-main' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("at-main") is None:
            self.prglog_mgr.debug("{}(): 'at-main' is required".format(GET_MY_NAME()))
            return False

        if cookies.get("x-main") is None:
            self.prglog_mgr.debug("{}(): 'x-main' is required for calling 'SKILLS' API".format(GET_MY_NAME()))
            return False

        self.prglog_mgr.info("{}(): Try to connect with cookies".format(GET_MY_NAME()))


        # Set headers and cookies
        self.auto.headers = HTTP_HEADER_ALEXA
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

        comms_id = ""  # for calling 'CONVERSATION' API

        # -----------------------------------------------------------------------------
        # Call internal APIs for getting user data
        for api in CIFTAmazonAlexaAPI:
            if api == CIFTAmazonAlexaAPI.UNKNOWN or api.code & 0x000001 == 0x000001:
                continue  # This API is used only for detecting cache entries

            # Set a default URL
            url = api.url
            if api == CIFTAmazonAlexaAPI.CARDS or api == CIFTAmazonAlexaAPI.ACTIVITIES:
                url = api.url.format("")
            elif comms_id != "" and \
                 (api == CIFTAmazonAlexaAPI.COMMS_CONTACTS or api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION):
                url = api.url.format(comms_id)
            elif comms_id == "" and \
                 (api == CIFTAmazonAlexaAPI.COMMS_CONTACTS or api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION):
                continue
            elif api == CIFTAmazonAlexaAPI.MEDIA_HISTORY:
                continue

            itemIds = []  # for calling sub-API of ACTIVITIES, NAMED_LIST and COMMS_CONVERSATION
            item_idx = 0
            iter_value = None

            while 1:
                if CIFT_DEBUG_CLOUD:
                    name = PtUtils.get_valid_filename("{}.json".format(url))
                    path = "{}/{}".format(self.path_base_dir, name)

                    if os.path.exists(path):
                        # Load the previous result for debugging
                        data = open(path).read()
                    else:
                        data = self.auto.get_text(url)
                        if data is None:
                            break
                        PtUtils.save_string_to_file(path, data)  # for debugging
                else:
                    data = self.auto.get_text(url)

                # Parse JSON format and Save the result to DB
                if data is not None:
                    try:
                        self.parser.process_api(
                            CIFTOperation.CLOUD, api, url=url, value=data, filemode=False,
                            base_path=self.path_base_dir
                        )
                    except:
                        pass

                # Check a few conditions for iteration
                if api != CIFTAmazonAlexaAPI.CARDS and \
                   api != CIFTAmazonAlexaAPI.ACTIVITIES and api != CIFTAmazonAlexaAPI.ACTIVITY_DIALOG_ITEM and \
                   api != CIFTAmazonAlexaAPI.NAMED_LIST and \
                   api != CIFTAmazonAlexaAPI.COMMS_ACCOUNTS and api != CIFTAmazonAlexaAPI.COMMS_CONVERSATION:
                    break

                if api == CIFTAmazonAlexaAPI.NAMED_LIST and len(itemIds) == item_idx and item_idx > 0:
                    break

                if api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION and len(itemIds) == item_idx and item_idx > 0:
                    break

                if api == CIFTAmazonAlexaAPI.CARDS:
                    # Read JSON format
                    data = PtUtils.read_json(data)
                    if data is None:
                        self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                        break

                    # For getting more 'CARDS'
                    value = data['nextQueryTime']
                    if value == -1:
                        break
                    self.prglog_mgr.info("{}(): \'nextQueryTime\' is {}".format(
                        GET_MY_NAME(), PtUtils.convert_unix_millisecond_to_str(value))
                    )
                    url = api.url.format(value)
                    continue

                # ---------------------------------------------------------------------
                # ACTIVITIES
                if api == CIFTAmazonAlexaAPI.ACTIVITIES and len(itemIds) == 0:
                    # Read JSON format
                    data = PtUtils.read_json(data)
                    if data is None:
                        self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                        break

                    # For getting more 'ACTIVITIES'
                    iter_value = data['startDate']
                    if iter_value is None:
                        break

                    if data.get('activities') is None:
                        if data.get('activity') is not None:
                            data['activities'] = [data.get('activity')]

                    for item in data.get('activities'):
                        itemIds.append(PtUtils.encode_url(item.get('id')))

                    if len(itemIds) > 0:
                        api = CIFTAmazonAlexaAPI.ACTIVITY_DIALOG_ITEM
                        url = api.url.format(itemIds[item_idx])
                        item_idx += 1
                    else:
                        break
                    continue

                elif api == CIFTAmazonAlexaAPI.ACTIVITY_DIALOG_ITEM and len(itemIds) > item_idx:
                    url = api.url.format(itemIds[item_idx])
                    item_idx += 1
                    continue

                elif api == CIFTAmazonAlexaAPI.ACTIVITY_DIALOG_ITEM and len(itemIds) == item_idx:
                    itemIds = []
                    item_idx = 0
                    if iter_value is None:
                        break
                    self.prglog_mgr.info("{}(): \'startDate\' is {}".format(
                        GET_MY_NAME(), PtUtils.convert_unix_millisecond_to_str(iter_value))
                    )
                    api = CIFTAmazonAlexaAPI.ACTIVITIES
                    url = api.url.format(iter_value)
                    continue
                # ---------------------------------------------------------------------

                # ---------------------------------------------------------------------
                # NAMED_LIST
                if api == CIFTAmazonAlexaAPI.NAMED_LIST and len(itemIds) == 0:
                    # Read JSON format
                    data = PtUtils.read_json(data)
                    if data is None:
                        self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                        break

                    # For getting detailed entries of each named list
                    for item in data.get("lists"):
                        itemIds.append(item.get('itemId'))
                    if len(itemIds) > 0:
                        url = api.url_sub.format(itemIds[item_idx])
                        item_idx += 1
                    continue

                elif api == CIFTAmazonAlexaAPI.NAMED_LIST and len(itemIds) > item_idx:
                    url = api.url_sub.format(itemIds[item_idx])
                    item_idx += 1
                    continue
                # ---------------------------------------------------------------------

                if api == CIFTAmazonAlexaAPI.COMMS_ACCOUNTS:
                    # Read JSON format
                    data = PtUtils.read_json(data)
                    if data is None:
                        self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                        break

                    # For getting 'commsId' of this account
                    if data[0] is not None:
                        if data[0]['commsId'] is not None:
                            comms_id = data[0]['commsId']
                    break

                # ---------------------------------------------------------------------
                # COMMS_CONVERSATION
                if api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION and len(itemIds) == 0:
                    # Read JSON format
                    data = PtUtils.read_json(data)
                    if data is None:
                        self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                        break

                    # For getting detailed entries of each conversation
                    for conv in data.get("conversations"):
                        itemIds.append(conv.get('conversationId'))
                    if len(itemIds) > 0:
                        url = api.url_sub.format(comms_id, itemIds[item_idx])
                        item_idx += 1
                    continue

                elif api == CIFTAmazonAlexaAPI.COMMS_CONVERSATION and len(itemIds) > item_idx:
                    url = api.url_sub.format(comms_id, itemIds[item_idx])
                    item_idx += 1
                    continue
                # ---------------------------------------------------------------------

        # -----------------------------------------------------------------------------
        # Traverse all alexa devices registered at the cloud service
        query = (AlexaDevice
                 .select(AlexaDevice.device_serial_number, AlexaDevice.device_type)
                 .group_by(AlexaDevice.device_serial_number))

        # Call internal APIs for getting user data
        api = CIFTAmazonAlexaAPI.MEDIA_HISTORY

        for record in query:
            if record.device_serial_number is None or\
               record.device_type is None:
                continue

            url = api.url.format(record.device_serial_number, record.device_type)

            if CIFT_DEBUG_CLOUD:
                name = PtUtils.get_valid_filename("{}.json".format(url))
                path = "{}/{}".format(self.path_base_dir, name)

                if os.path.exists(path):
                    # Load the previous result for debugging
                    data = open(path).read()
                else:
                    data = self.auto.get_text(url)
                    if data is None:
                        continue
                    PtUtils.save_string_to_file(path, data)
            else:
                data = self.auto.get_text(url)

            # Parse JSON format and Save the result to DB
            if data is not None:
                try:
                    self.parser.process_api(
                        CIFTOperation.CLOUD, api, url=url, value=data, filemode=False,
                        base_path=self.path_base_dir
                    )
                except:
                    pass

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
        self.prglog_mgr.info("{}(): Download voice data from Amazon Alexa cloud service".format(GET_MY_NAME()))

        query = (Timeline
                 .select(Timeline.date, Timeline.time, Timeline.timezone, Timeline.desc, Timeline.extra)
                 .where(Timeline.extra.contains(URL_PREFIX_ALEXA_AUDIO_RAW))
                 .order_by(Timeline.date.desc(), Timeline.time.desc()))

        # [To-do]
        # Downloading conversation (audio message) voice files is not supported currently,
        # because 'SIP_AUTH_TOKEN' is required for accessing the Amazon's SIP server but
        # the value is encrypted and stored in SECURED_SHARED_PREFS.xml. (cf. Android KeyStore)
        # Thus, we need to find out a way to decrypt the token value.
        #
        # query = (Timeline
        #          .select(Timeline.date, Timeline.time, Timeline.timezone, Timeline.desc, Timeline.extra)
        #          .where(Timeline.extra.contains(URL_PREFIX_ALEXA_AUDIO_RAW) |
        #                 Timeline.extra.contains(URL_PREFIX_ALEXA_CONVERSATION_AUDIO_RAW))
        #          .order_by(Timeline.date.asc(), Timeline.time.asc()))

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

            voice_url = voice_url.replace("\"", "")
            voice_url = voice_url.replace(" ", "")

            if voice_url.startswith(URL_PREFIX_ALEXA_AUDIO_RAW):
                # --------------------------------------------
                # Tokenize voice ID
                #
                voice_id = voice_url.replace(URL_PREFIX_ALEXA_AUDIO_RAW, "")
                items = voice_id.split(":")
                if len(items) != 5:
                    self.prglog_mgr.debug("{}(): Invalid Voice ID ({})".format(GET_MY_NAME(), voice_id))
                    continue

                type = items[0]
                date = items[1]
                tsec = items[2]
                guid = items[4]

                # Get a timestamp from voice ID
                items = date.split("/")
                if len(items) != 7:
                    self.prglog_mgr.debug("{}(): Invalid Voice ID ({})".format(GET_MY_NAME(), voice_id))
                    continue

                created_timestamp = "{}-{}-{}T{}:{}:{}Z".format(items[1], items[2], items[3], items[4], items[6], tsec)
                d, t = PtUtils.convert_iso8602_to_str(created_timestamp, millisecond=False)
                created_timestamp = PtUtils.make_iso8602(d, t, millisecond=False)

                # Set a output file path
                desc = record.desc if len(record.desc) < 65 else record.desc[:63] + "..."
                if desc == "" or desc == "-":
                    desc = "TRANSCRIPT NOT AVAILABLE"  # Text not available. Click to play recording. (Alexa's History)
                # meta = "({})_TYPE({})_SN({})_({})".format(created_timestamp, type, items[5], desc)
                meta = "({})_TEXT({})".format(created_timestamp, desc)
                name = PtUtils.get_valid_filename(meta)
                path = "{}/VOICE/{}.wav".format(self.path_base_dir, name)

            # elif voice_url.startswith(URL_PREFIX_ALEXA_CONVERSATION_AUDIO_RAW):
            #     # Set a output file path
            #     meta = "({} {})_MSG({})".format(record.date, record.time, record.desc)
            #     name = PtUtils.get_valid_filename(meta)
            #     path = "{}/AUDIO_MESSAGE/{}.mp3".format(self.path_base_dir, name)

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

        url = "https://alexa.amazon.com"
        if self.auto.visit(url) is False:
            return False

        # Set cookies
        tmp_name = PtUtils.generate_str_with_time("cookies.js")
        self.auto.save_cookies(tmp_name)
        self.auto.browser.delete_all_cookies()
        self.auto.load_cookies(tmp_name)

        # Try to login with ID and PW
        element = self.auto.browser.find_element_by_id("ap_email")
        element.send_keys(self.user_id)
        element = self.auto.browser.find_element_by_id("ap_password")
        element.send_keys(self.user_pw)
        # self.auto.browser.save_screenshot('screenshot-1.png')
        # b64 = self.auto.browser.get_screenshot_as_base64()
        element.send_keys(self.auto.keys.RETURN)
        self.auto.browser.implicitly_wait(5)
        time.sleep(3)

        # self.auto.browser.save_screenshot('screenshot-2.png')
        # b64 = self.auto.browser.get_screenshot_as_base64()
        current_url = self.auto.browser.current_url
        title = self.auto.browser.title
        page_source = self.auto.browser.page_source
        # self.prglog_mgr.info("{}(): The current page's title is '{}'".format(GET_MY_NAME(), title))

        if page_source.find("Your password is incorrect") > 0:
            self.prglog_mgr.info("{}(): Login failed - Your password is incorrect".format(GET_MY_NAME()))
            return False

        if title != "Amazon Alexa":  # Experimental
            # The following codes are working, but the login fails...
            self.auto.browser.save_screenshot('screenshot-captcha.png')
            self.prglog_mgr.info("{}(): Login failed - You may handle the CAPTCHA system".format(GET_MY_NAME(), title))
            captcha_guess = input("Enter a CAPTCHA: ")

            # Try to login with ID and PW
            element = self.auto.browser.find_element_by_id("ap_password")
            element.send_keys(self.user_pw)

            element = self.auto.browser.find_element_by_id("ap_captcha_guess")
            element.send_keys(captcha_guess)

            self.auto.browser.save_screenshot('screenshot-debug-1.png')
            element.send_keys(self.auto.keys.RETURN)
            self.auto.browser.implicitly_wait(5)
            time.sleep(3)
            self.auto.browser.save_screenshot('screenshot-debug-2.png')

            title = self.auto.browser.title
            self.prglog_mgr.info("{}(): The current page's title is '{}'".format(GET_MY_NAME(), title))

            if title != "Amazon Alexa":
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

        text = self.auto.get_text(CIFTAmazonAlexaAPI.BOOTSTRAP.url)
        if text is None:
            return False

        if not text.startswith("{"):
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


class AmazonAlexaClient:
    """AmazonAlexaClient class

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
        self.parser = AmazonAlexaParser(path_base_dir, delete_db=False)
        # self.parser = AmazonAlexaParser(path_base_dir, delete_db=True)

        # class variables
        self.path_base_dir = "{}/{}/{}".format(path_base_dir, EVIDENCE_LIBRARY, __class__.__name__)
        PtUtils.make_dir(self.path_base_dir)

        # Progress logging manager
        self.prglog_mgr = logging.getLogger(__name__)

    def run(self, op, path):
        """Search and interpret Amazon Alexa related data stored within companion devices

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (directory or file)

        Returns:
            True or False
        """
        self.prglog_mgr.info(
            "{}(): Process Amazon Alexa related data stored within companion clients".format(GET_MY_NAME())
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

        if op is CIFTOperation.COMPANION_APP_ANDROID:
            ret = self.process_app_android(op, path)

        elif op is CIFTOperation.COMPANION_APP_IOS:
            ret = self.process_app_ios(op, path)

        elif op is CIFTOperation.COMPANION_BROWSER_CHROME:
            ret = self.process_chromium_main_disk_cache(op, path)

        elif CIFTOperation.COMPANION_RAM < op:
            ret = self.scan(op, path)

        return ret

    def process_app_android(self, op, path):
        """Search and interpret Amazon Alexa related data stored within Android devices

            [ANDROID]
            - com.amazon.dee.app

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (= the target directory)

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # --------------------------------
        # [Cookies]
        # ./app_webview/Cookies
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.ANDROID_COOKIES,
            path + "/app_webview/Cookies",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [DataStore.db]
        # ./databases/DataStore.db
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.ANDROID_DATASTORE,
            path + "/databases/DataStore.db",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [map_data_storage.db]
        # ./databases/map_data_storage.db
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE,
            path + "/databases/map_data_storage.db",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [map_data_storage_v2.db]
        # ./databases/map_data_storage_v2.db
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.ANDROID_MAP_DATA_STORAGE_V2,
            path + "/databases/map_data_storage_v2.db",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [Chromium WebView cache]
        # ./app_webview/Cache/
        self.process_chromium_simple_disk_cache(op, path + "/app_webview/cache/")

        # --------------------------------
        # [Chromium WebView cache]
        # ./cache/org.chromium.android_webview/
        self.process_chromium_simple_disk_cache(op, path + "/cache/org.chromium.android_webview/")

        # --------------------------------
        # [Chrome Cache] - any meaningful traces?
        # ./app_webview/Application Cache/Cache/
        self.process_chromium_main_disk_cache(op, path + "/app_webview/Application Cache/Cache/")

        # --------------------------------
        # [Cached voice data]
        # ./cache/sound                    ---> Recently played audio data from History
        self.acquire_file(op, path + "/cache/sound", "wav", "Recently played audio data from History")

        # --------------------------------
        # [Cached voice data]
        # ./files/audio_cache/{mediaId}.1  ---> Cached voice messages (audio files)
        self.acquire_cached_voice_data_android(op, path + "/files/audio_cache/")

        # --------------------------------
        # [Error logs]
        # ./app_901ad8be11e4424f875dc792db51f34d515d6767-01b7-49e5-8273-c8d11b0f331d\events\eventsFile
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.ANDROID_EVENTSFILE,
            path + "/app_901ad8be11e4424f875dc792db51f34d515d6767-01b7-49e5-8273-c8d11b0f331d/events/eventsFile",
            base_path=self.path_base_dir
        )

        return True

    def process_app_ios(self, op, path):
        """Search and interpret Amazon Alexa related data stored within iOS devices

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (= the target directory)

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        # --------------------------------
        # [LocalData.db]
        # ./Documents/LocalData.sqlite
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.IOS_LOCALDATA,
            path + "/Documents/LocalData.sqlite",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [AlexaMobileiOSComms.sqlite]
        # ./Documents/AlexaMobileiOSComms.sqlite
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.IOS_COMMS,
            path + "/Documents/AlexaMobileiOSComms.sqlite",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [Cookies.binarycookies]
        # ./Library/Cookies/Cookies.binarycookies
        self.parser.process_client_file(
            op, CIFTAmazonAlexaClientFile.IOS_COOKIES,
            path + "/Library/Cookies/Cookies.binarycookies",
            base_path=self.path_base_dir
        )

        # --------------------------------
        # [Cached voice data]
        # ./Documents/Record-{Timestamp}.*
        # ./Documents/Download_{Timestamp}.*
        self.acquire_cached_voice_data_ios(op, path + "/Documents/")

        return True

    def acquire_file(self, op, path, ext="", desc=""):
        """Acquire file(s) with user-defined conditions

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data
            ext (str): The extension for storing the target file
            desc (str): The description for explaining the target file

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) PATH({})".format(GET_MY_NAME(), op.name, path))

        if not os.path.exists(path):
            self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
            return False

        # --------------------------------------------
        # Save this data to Evidence Library
        name = "{} {}".format(path, PtUtils.get_random())
        name = PtUtils.hash_sha1(name.encode('utf-8'))
        path_dst = "{}/{}.{}".format(self.path_base_dir, name, ext)

        self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path_dst))
        PtUtils.copy_file(path, path_dst)

        # --------------------------------------------
        # Insert a record into 'ACQUIRED_DATA' table
        #
        operation_id = -1
        query = Operation.select().where(Operation.type == op.name)

        if len(query) == 1:
            operation_id = query[0].id

        d, t = PtUtils.get_file_created_date_and_time(path_dst)
        saved_timestamp = "{} {}".format(d, t)
        # d, t = PtUtils.get_file_modified_date_and_time(path_dst)
        # modified_timestamp = "{} {}".format(d, t)

        AcquiredFile.create(
            operation_id=operation_id,
            src_path=path,
            desc=desc,
            saved_path=path_dst,
            sha1=PtUtils.hash_sha1(path_dst, filemode=True),
            saved_timestamp=saved_timestamp,
            modified_timestamp="-",
            timezone=PtUtils.get_timezone()
        )

        return True

    def acquire_cached_voice_data_android(self, op, path):
        """Acquire file(s) with user-defined conditions

        Args:
            op (CIFTOperation): The current operation
            path (str): The directory path of having cached voice data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) PATH({})".format(GET_MY_NAME(), op.name, path))

        base_path = path

        if not os.path.exists(base_path):
            self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
            return False

        for file_name in os.listdir(base_path):
            if not file_name.endswith(".1"):
                continue

            file_path = os.path.join(base_path, file_name)
            file_size = os.path.getsize(file_path)

            if file_size < 128:
                continue

            try:
                file_object = open(file_path, 'rb')
            except IOError as exception:
                self.prglog_mgr.debug("{}(): Exception occurred".format(GET_MY_NAME()))
                continue

            data = file_object.read()
            file_object.close()

            if data[4:8].startswith(SIG_MP4):
                ext = "m4a"
            elif data[0:2].startswith(SIG_MP3):
                ext = "mp3"
            else:
                self.prglog_mgr.info("{}(): Unknown audio format".format(GET_MY_NAME()))
                ext = "unknown-format"

            # --------------------------------------------
            # Save this data to Evidence Library
            name = "{} {}".format(file_path, PtUtils.get_random())
            name = PtUtils.hash_sha1(name.encode('utf-8'))
            path_dst = "{}/{}.{}".format(self.path_base_dir, name, ext)

            self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path_dst))
            PtUtils.copy_file(file_path, path_dst)

            # --------------------------------------------
            # Insert a record into 'ACQUIRED_DATA' table
            #
            operation_id = -1
            query = Operation.select().where(Operation.type == op.name)

            if len(query) == 1:
                operation_id = query[0].id

            d, t = PtUtils.get_file_created_date_and_time(path_dst)
            saved_timestamp = "{} {}".format(d, t)
            # d, t = PtUtils.get_file_modified_date_and_time(path_dst)
            # modified_timestamp = "{} {}".format(d, t)

            AcquiredFile.create(
                operation_id=operation_id,
                src_path=file_path,
                desc="Cached voice data ({})".format(ext),
                saved_path=path_dst,
                sha1=PtUtils.hash_sha1(path_dst, filemode=True),
                saved_timestamp=saved_timestamp,
                modified_timestamp="-",
                timezone=PtUtils.get_timezone()
            )

        return True

    def acquire_cached_voice_data_ios(self, op, path):
        """Acquire file(s) with user-defined conditions

        Args:
            op (CIFTOperation): The current operation
            path (str): The directory path of having cached voice data

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}(): OP({}) PATH({})".format(GET_MY_NAME(), op.name, path))

        base_path = path

        if not os.path.exists(base_path):
            self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
            return False

        for file_name in os.listdir(base_path):
            if not (file_name.startswith("Download_") or file_name.startswith("Record-")):
                continue

            file_path = os.path.join(base_path, file_name)
            file_size = os.path.getsize(file_path)

            if file_size < 128:
                continue

            try:
                file_object = open(file_path, 'rb')
            except IOError as exception:
                self.prglog_mgr.debug("{}(): Exception occurred".format(GET_MY_NAME()))
                continue

            data = file_object.read()
            file_object.close()

            if data[4:8].startswith(SIG_MP4):
                ext = "m4a"
            elif data[0:2].startswith(SIG_MP3):
                ext = "mp3"
            else:
                self.prglog_mgr.info("{}(): Unknown audio format".format(GET_MY_NAME()))
                ext = "unknown-format"

            # --------------------------------------------
            # Save this data to Evidence Library
            name = "{} {}".format(file_path, PtUtils.get_random())
            name = PtUtils.hash_sha1(name.encode('utf-8'))
            path_dst = "{}/{}.{}".format(self.path_base_dir, name, ext)

            self.prglog_mgr.info("{}(): Saved path is {}".format(GET_MY_NAME(), path_dst))
            PtUtils.copy_file(file_path, path_dst)

            # --------------------------------------------
            # Insert a record into 'ACQUIRED_DATA' table
            #
            operation_id = -1
            query = Operation.select().where(Operation.type == op.name)

            if len(query) == 1:
                operation_id = query[0].id

            d, t = PtUtils.get_file_created_date_and_time(path_dst)
            saved_timestamp = "{} {}".format(d, t)
            # d, t = PtUtils.get_file_modified_date_and_time(path_dst)
            # modified_timestamp = "{} {}".format(d, t)

            AcquiredFile.create(
                operation_id=operation_id,
                src_path=file_path,
                desc="Cached voice data ({})".format(ext),
                saved_path=path_dst,
                sha1=PtUtils.hash_sha1(path_dst, filemode=True),
                saved_timestamp=saved_timestamp,
                modified_timestamp="-",
                timezone=PtUtils.get_timezone()
            )

        return True

    def process_chromium_main_disk_cache(self, op, path):
        """Search and interpret Amazon Alexa related data stored within Android devices

            < Chrome Cache format >
                - ComponentComponents
                    - index: Index
                    - data_0, data_1, data_2, data_3: URL, Cache name, cache data
                    - f_OOOOOO: Cache data files
                - Parsing steps
                    - Parsing an index file
                    - Access cache entries
                    - Go to all data streams
                    - Find GZIP header
                    - Decompress
                    - Discriminate JSON data by URL or content

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (= the target directory)

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if not os.path.exists(path):
            self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
            return False

        path_root = path

        chrome_cache = ChromiumMainCache()
        chrome_cache.set_url_pattern('https://[a-z-]+.amazon.com/(api|app)/')

        if chrome_cache.parse(path_root) is False:
            return False

        cache_entry = MainCacheEntry()

        # Traverse all cache entries relating to Amazon Alexa
        for cache_entry in chrome_cache.cache_entries:
            url = cache_entry.key

            # Check all data streams
            for idx in range(len(cache_entry.data_stream_addresses)):
                data_stream_size = cache_entry.data_stream_sizes[idx]
                data_stream_addr = cache_entry.data_stream_addresses[idx]

                if data_stream_addr == 0:
                    break

                if data_stream_size < 8:
                    continue

                data_file = path_root + "/{}".format(data_stream_addr.filename)

                try:
                    file_object = open(data_file, 'rb')
                    if data_stream_addr.block_offset is not None:
                        file_object.seek(data_stream_addr.block_offset, os.SEEK_SET)
                except IOError as exception:
                    self.prglog_mgr.debug("{}(): Cannot open the file ({})".format(GET_MY_NAME(), data_file))
                    continue

                data = file_object.read(data_stream_size)
                file_object.close()

                if not data[0:2].startswith(SIG_GZIP):
                    continue

                body = PtUtils.decompress_gzip(data)
                if len(body) < 4:
                    continue

                if not (body[0:1] == b'{' or body[0:1] == b'['):
                    continue  # Process JSON format only

                try:
                    body = body.decode("utf-8")
                except UnicodeDecodeError:
                    self.prglog_mgr.debug("{}(): Invalid JSON format".format(GET_MY_NAME()))
                    continue

                # Check if this JSON is supported by the 'Parser' module
                api = self.identify_alexa_api(url)

                # Parse JSON format and Save the result to DB
                try:
                    self.parser.process_api(
                        op, api, url=url, value=body, filemode=False,
                        base_path=self.path_base_dir
                    )
                except:
                    pass

        chrome_cache.close()
        return True

    def process_chromium_simple_disk_cache(self, op, path):
        """Search and interpret Amazon Alexa related data stored within Android devices

            < Android web cache format >
                - Parsing steps
                    - Find GZIP header
                    - Decompress
                    - Discriminate JSON data by URL or content

            [ANDROID]
            - com.amazon.dee.app/app_webview/Cache/*

        Args:
            op (CIFTOperation): The current operation
            path (str): The path of the input data (= the target directory)

        Returns:
            True or False
        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if not os.path.exists(path):
            self.prglog_mgr.debug("{}(): The path does not exist ({})".format(GET_MY_NAME(), path))
            return

        path_target = path
        cache_entry = SimpleCacheEntry()

        # Traverse all files in a target directory
        for root, dirs, files in os.walk(path_target):
            for file in files:
                file_path = os.path.join(root, file)

                simple_cache = ChromiumSimpleCache()

                if simple_cache.parse(file_path) is False:
                    continue

                cache_entry = simple_cache.cache_entry

                if cache_entry.key == "" or len(cache_entry.streams) == 0:
                    continue

                for stream in cache_entry.streams:
                    if not stream.startswith(SIG_GZIP):
                        continue

                    body = PtUtils.decompress_gzip(stream)
                    if len(body) < 4:
                        continue

                    if not (body[0:1] == b'{' or body[0:1] == b'['):
                        continue  # Process JSON format only

                    try:
                        body = body.decode("utf-8")
                    except UnicodeDecodeError:
                        self.prglog_mgr.debug("{}(): Not valid JSON format".format(GET_MY_NAME()))
                        continue

                    # Check if this JSON is supported by the 'Parser' module
                    api = self.identify_alexa_api(cache_entry.key)

                    # Parse JSON format and Save the result to DB
                    try:
                        self.parser.process_api(
                            op, api, url=cache_entry.key, value=body,
                            filemode=False, base_path=self.path_base_dir
                        )
                    except:
                        pass

        return True

    def identify_alexa_api(self, url):
        """Identify an Alexa API from a URL

        Args:
            url (str): The URL

        Returns:
            CIFTAmazonAlexaAPI
        """
        self.prglog_mgr.info("{}(): {}".format(GET_MY_NAME(), url))

        for api in CIFTAmazonAlexaAPI:
            if api == CIFTAmazonAlexaAPI.UNKNOWN:
                continue

            base = api.url.replace('{}', '?')
            base = base.split('?')[0]
            comp = url.split('?')[0]

            if comp.startswith(base):
                if api == CIFTAmazonAlexaAPI.TASK_LIST:
                    base = api.url.split('&')[0]
                    comp = url.split('&')[0]
                    if comp.startswith(base):
                        return api
                return api

            for alter in PREFIX_ALEXA_API_ALTERNATIVES:
                base = api.url.replace('{}', '?')
                base = base.replace(PREFIX_ALEXA_API, alter).split('?')[0]
                comp = url.split('?')[0]

                if comp.startswith(base):
                    if api == CIFTAmazonAlexaAPI.TASK_LIST:
                        base = api.url.split('&')[0]
                        comp = url.split('&')[0]
                        if comp.startswith(base):
                            return api
                    return api

        return CIFTAmazonAlexaAPI.UNKNOWN

    def scan(self, op, path):
        """TODO

            - RAM dump

        Args:
            path (str): The path of the input data (= RAM dump file)

        Returns:
            True or False
        """
        return True

    def close(self):
        """Post-process

        """
        self.prglog_mgr.info("{}()".format(GET_MY_NAME()))

        if self.parser is not None:
            self.parser.close()
        return

