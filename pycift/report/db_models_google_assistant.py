"""pycift.report.db_models_google_assistant

    * Description
        Output DB models for parsing results on Google Assistant forensics
"""

import logging

from peewee import *
from playhouse.sqlite_ext import PrimaryKeyAutoIncrementField
from playhouse.csv_utils import dump_csv
logger = logging.getLogger('peewee')
logger.setLevel(logging.WARNING)

from pycift.common_defines import *
from pycift.utility.pt_utils import PtUtils


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
        0  | CLOUD | https://~ | MyActivity | d:\1.jspb | 1234***4321 | 2016-12-13 00:00:00 | -
        1  | CLOUD | https://~ | MyActivity | d:\2.jspb | 2345***5432 | 2016-12-13 00:00:05 | -
        3  | CLOUD | https://~ | Voice      | d:\3.mp3  | abcd***efgh | 2017-06-28 21:00:07 | -
        3  | CLOUD | https://~ | Voice      | d:\4.mp3  | abcd***efgh | 2017-06-28 21:00:07 | -
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
    - CREDENTIAL (Cookies)
        type | domain | value | $source_id
        Android Cookie | .amazon.com | set of cookie entries |
        iOS Cookie     | .amazon.com | set of cookie entries |
        iOS Cookie     | .google.com | set of cookie entries |
    """
    type = TextField()
    domain = TextField()
    value = TextField()
    source = ForeignKeyField(AcquiredFile)

    class Meta:
        primary_key = False
        db_table = 'CREDENTIAL'


class Timeline(Model):
    """
    - TIMELINE (MyActivity)
        date | time | timezone | MACB | source | sourcetype | type | user | host | short |
        desc | version | filename | inode | notes | format | extra
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

        self.db_path = db_path
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
                               Credential, Timeline])
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
        prefix = CIFT_GOOGLE_ASSISTANT

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

        query = Timeline.select()
        if len(query) > 0:
            path = '{}/{}_{}.csv'.format(base, prefix, Timeline._meta.db_table)
            with open(path, "w", newline="\n", encoding="utf-8") as fh:
                dump_csv(query, fh)

    def close(self):
        """Close this module

        """
        self.db.close()

