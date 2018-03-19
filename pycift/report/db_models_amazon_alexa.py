"""pycift.report.db_models_amazon_alexa

    * Description
        Output DB models for parsing results on Amazon Alexa forensics
"""

import logging

from peewee import *
from playhouse.sqlite_ext import PrimaryKeyAutoIncrementField
from playhouse.csv_utils import dump_csv
logger = logging.getLogger('peewee')
logger.setLevel(logging.WARNING)

from pycift.common_defines import *
from pycift.utility.pt_utils import PtUtils

# [ References for peewee ]
# https://peewee.readthedocs.io/en/2.0.2/peewee/fields.html
# http://docs.peewee-orm.com/en/latest/peewee/database.html
# http://docs.peewee-orm.com/en/latest/peewee/example.html#running-the-example
# https://github.com/coleifer/peewee/blob/master/examples/diary.py
# http://stackoverflow.com/questions/39131122/using-command-line-arguments-in-imported-module


class Operation(Model):
    """
    - OPERATION
        *no | type
        ------------------------------
        0  | HARDWARE
        1  | HARDWARE_FILES
        2  | HARDWARE_RAM
        3  | CLOUD
        4  | COMPANION
        5  | COMPANION_APP_ANDROID
        6  | COMPANION_APP_IOS
        7  | COMPANION_BROWSER_CHROME
        8  | COMPANION_RAM
    """
    id = PrimaryKeyAutoIncrementField()
    type = TextField()

    class Meta:
        db_table = 'OPERATION'


class AcquiredFile(Model):
    """
    - ACQUIRED_FILE
        *no | $operation | src_path | desc | saved_path | sha1 | saved_timestamp | modified_timestamp | timezone
         0  | CLOUD | https://~ | Activities | d:\1.json | 1234***4321 | 2016-12-13 00:00:00 | -
         1  | CLOUD | https://~ | Cards      | d:\2.json | 2345***5432 | 2016-12-13 00:00:05 | -
    """
    id = PrimaryKeyAutoIncrementField()
    operation = ForeignKeyField(Operation)  # operation type
    src_path = TextField()
    desc = TextField()
    saved_path = TextField()
    sha1 = TextField()
    saved_timestamp = TextField()
    modified_timestamp = TextField()
    timezone = TextField()

    class Meta:
        db_table = 'ACQUIRED_FILE'


class Credential(Model):
    """
    - CREDENTIAL (Cookies + External auth list)
        type | domain | values | $source_id
        Android Cookie | .amazon.* | values | s_id
        iOS Cookie     | .amazon.* | values | s_id
    """
    type = TextField()
    domain = TextField()
    value = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'CREDENTIAL'


class Account(Model):
    """
    - ACCOUNT (BOOTSTRAP + HOUSEHOLD + COMMS_ACCOUNTS)
        customer_email | customer_name | phone_number | customer_id | comms_id | authenticated | $source_id
    """
    customer_email = TextField(null=True)
    customer_name = TextField()
    phone_number = TextField(null=True)
    customer_id = TextField(null=True)
    comms_id = TextField(null=True)
    authenticated = TextField(null=True)
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'ACCOUNT'


class Contact(Model):
    """
    - CONTACT (COMMS_CONTACTS)
        first_name | last_name | number | email | is_home_group | contact_id | comms_id | $source_id
    """
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    number = TextField(null=True)
    email = TextField(null=True)
    is_home_group = TextField()
    contact_id = TextField()
    comms_id = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'CONTACT'


class SettingWifi(Model):
    """
    - SETTING_WIFI
        ssid | security_method | pre_shared_key | $source_id
    """
    ssid = TextField()
    security_method = TextField()
    pre_shared_key = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'SETTING_WIFI'


class SettingMisc(Model):
    """
    - SETTING_MISC
        name | value | device_serial_number | $source_id
        traffic_origin_address | origin.label |
        traffic_waypoint | waypoints[0].label |
        traffic_destination_address | destination.label |
        calendar_account | householdAccountList[0].getCalendarAccountsResponse |
        wake_word | wakeWords[0].wakeWord | wakeWords[0].deviceSerialNumber
        paired_bluetooth_device | bluetoothStates[0].pairedDeviceList | bluetoothStates[0].deviceSerialNumber
        third_party_service | services[0].serviceName
    """
    name = TextField()
    value = TextField()
    device_serial_number = TextField(null=True)
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'SETTING_MISC'


class AlexaDevice(Model):
    """
    - ALEXA_DEVICE (Devices + Device Preferences) -> Echo, Fire TV
        device_account_name | device_account_id | customer_id | device_serial_number | device_type |
        sw_version | mac_address | address | postal_code | locale | search_customer_id |
        timezone | region | $source_id
    """
    device_account_name = TextField(null=True)
    device_family = TextField(null=True)
    device_account_id = TextField()
    customer_id = TextField(null=True)
    device_serial_number = TextField()
    device_type = TextField()
    sw_version = TextField(null=True)
    mac_address = TextField(null=True)
    address = TextField(null=True)
    postal_code = IntegerField(null=True)
    locale = TextField(null=True)
    search_customer_id = TextField(null=True)
    timezone = TextField(null=True)
    region = TextField(null=True)
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'ALEXA_DEVICE'


class CompatibleDevice(Model):
    """
    - COMPATIBLE_DEVICE (Phoenix) -> Hue Lamps, Bright, Wemo...
        name | manufacture | model | created | last_seen | name_modified |
        desc | type | reachable | firmware_version | appliance_id |
        alexa_device_serial_number | alexa_device_type | $source_id
    """
    name = TextField()
    manufacture = TextField()
    model = TextField(null=True)
    created = TextField()
    # last_seen = TextField()  # this has no meaning
    name_modified = TextField()
    desc = TextField(null=True)
    type = TextField(null=True)
    reachable = TextField(null=True)
    firmware_version = TextField(default="", null=True)
    appliance_id = TextField()
    alexa_device_serial_number = TextField()
    alexa_device_type = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'COMPATIBLE_DEVICE'


class Skill(Model):
    """
    - SKILL
        title | developer_name | account_linked | release_date | short |
        desc | vendor_id | skill_id | $source_id
    """
    title = TextField()
    developer_name = TextField(null=True)
    account_linked = TextField()
    release_date = TextField()
    short = TextField()
    desc = TextField()
    vendor_id = TextField()
    skill_id = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'SKILL'


class Timeline(Model):
    """
    - TIMELINE (Activities + Cards + Media + Task list + Shopping list + Notifications...)
        date | time | timezone | MACB | source | sourcetype | type | user | host |
        short | desc | version | filename | inode | notes | format | extra
    """
    date = TextField()
    time = TextField()
    timezone = TextField()

    MACB = TextField()
    source = TextField()
    sourcetype = TextField()
    type = TextField()

    user = TextField(default="-")
    host = TextField(default="-")

    short = TextField(default="-")
    desc = TextField(default="-")

    version = IntegerField(default=2)
    filename = TextField()  # ForeignKeyField(AcquiredFile)
    inode = IntegerField(null=True)

    notes = TextField(default="-")
    format = TextField()
    extra = TextField(default="-")

    class Meta:
        primary_key = False
        db_table = 'TIMELINE'


class DatabaseManager(object):
    """DatabaseManager class

    Attributes:
        db (SqliteDatabase): The module for handling SQLite database format
    """

    def __init__(self, db_path, delete_db=True):
        """The constructor
        """
        if CIFT_DEBUG is True and delete_db is True:
            PtUtils.delete_file(db_path)

        self.db = SqliteDatabase(db_path, pragmas=(
            ('journal_mode', 'OFF'),
            ('synchronous', 'OFF')
            # ('cache_size', 10000),
            # ('mmap_size', 1024 * 1024 * 32)
        ))

        self.update_database()
        self.db.connect()

        # cursor = self.db.get_cursor()
        # # cursor.execute("PRAGMA journal_mode = OFF")
        # # cursor.execute("PRAGMA cache_size = 10000")
        # # cursor.execute("PRAGMA synchronous = off")
        # cursor.close()

        if len(self.db.get_tables(Operation)) != 0:
            return

        self.db.create_tables([Operation, AcquiredFile,
                               Credential, Account, Contact,
                               SettingWifi, SettingMisc,
                               AlexaDevice, CompatibleDevice, Skill,
                               Timeline])
        self.populate_default_tables()
        self.db.commit()
        self.db.close()
        return

    def update_database(self):
        """Update the 'database' member of all models

        """
        Operation._meta.database = self.db
        AcquiredFile._meta.database = self.db
        Credential._meta.database = self.db
        Account._meta.database = self.db
        Contact._meta.database = self.db
        SettingWifi._meta.database = self.db
        SettingMisc._meta.database = self.db
        AlexaDevice._meta.database = self.db
        CompatibleDevice._meta.database = self.db
        Skill._meta.database = self.db
        Timeline._meta.database = self.db

    def populate_default_tables(self):
        """Populate default tables (models)

            - 'Component' table
        """
        for op in CIFTOperation:
            Operation.create(type=op.name)

    def dump_csv(self, base):
        """Dump all tables to csv files

        Args:
            base (str): The base directory path
        """
        # with open('{}/{}.csv'.format(base, Operation._meta.db_table), "w", newline="\n", encoding="utf-8") as fh:
        #     query = Operation.select()
        #     dump_csv(query, fh)

        prefix = CIFT_AMAZON_ALEXA

        query = AcquiredFile \
                .select(AcquiredFile.id,
                    Operation.type.alias('operation_type'),
                    AcquiredFile.src_path,
                    AcquiredFile.desc,
                    AcquiredFile.saved_path,
                    AcquiredFile.sha1,
                    AcquiredFile.saved_timestamp,
                    AcquiredFile.modified_timestamp,
                    AcquiredFile.timezone) \
            .join(Operation)
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, AcquiredFile._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = Credential.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Credential._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = Account.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Account._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = Contact.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Contact._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = SettingWifi.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, SettingWifi._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = SettingMisc.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, SettingMisc._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = AlexaDevice.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, AlexaDevice._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = CompatibleDevice.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, CompatibleDevice._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = Skill.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Skill._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

        query = Timeline.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Timeline._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

    def close(self):
        """Close this module

        """
        self.db.close()

