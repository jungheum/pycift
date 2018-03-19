"""pycift: A Python implementation of CIFT

    * Description
        A Python implementation of CIFT (Cloud-based IoT Forensic Toolkit)

    * Author
        Hyunji Chung  <localchung@gmail.com>
        Jungheum Park <junghmi@gmail.com>

    * License
        Apache License 2.0

    * Tested Python Versions
        Python 3.5

    * Tested Operating Systems
        Windows 10 Home 64-bits English
        (Linux & OSX -> test required)

    * Requirements - Python packages
        selenium
        python-dateutil
        requests
        construct
        peewee (for SQLite)
        iso8601
        pypiwin32 (Windows only)

    * Requirements - Binaries
        PHANTOMJS (Windows)
            - Assume that the base path is "C:\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe"
            - The path needs to be changed --> see 'pycift/utility/browser_automation.py'
        ChromeDriver
            - Get the latest version (https://sites.google.com/a/chromium.org/chromedriver/downloads)

    * History
        0.1.20161130
            - Started the implementation of pycift
            - Built the overall structure of CIFT (Cloud-based Forensic Toolkit)
            - Designed reporting modules
            - Added browser automation module (IDPW login)
        0.1.20161218
            - Added cloud data acquisition modules for Amazon Alexa
            - Added parsing modules for cloud native artifacts related to Amazon Alexa
        0.2.20170111
            - Updated parsing modules for cloud native artifacts related to Amazon Alexa
            - Added parsing modules for client centric artifacts related to Amazon Alexa
        0.2.20170129
            - Updated parsing modules of Amazon Alexa
        0.3.20170415
            - Updated cloud data acquisition modules for Amazon Alexa
            - Updated parsing modules of Amazon Alexa
        0.3.20170704
            - Updated parsing modules of Amazon Alexa
        0.4.20170802
            - Unofficial release for DFRWS USA 2017 demo
        0.5.20170919
            - Started writing modules for Google Assistant
            - Added cloud data acquisition modules for Google Assistant
        0.5.20171030
            - Updated cloud data acquisition modules for Google Assistant
        0.5.20171102
            - Updated browser automation module (COOKIE login)
            - Updated cloud data acquisition modules for Amazon Alexa and Google Assistant
        0.6.20180117
            - Updated cloud data acquisition modules for Amazon Alexa (new APIs including messaging and calling)
        0.6.20180125
            - Added parsing modules for client centric artifacts related to Google Assistant
        0.6.20180214
            - Updated parsing modules of Amazon Alexa and Google Assistant
        0.6.20180205
            - Updated cloud data acquisition modules for Amazon Alexa and Google Assistant
            - Updated parsing modules of Amazon Alexa and Google Assistant
        0.6.20180224
            - Tested and enhanced with various data from multiple sources
        1.0.20180318
            - The first release to the public (https://bitbucket.org/cift/pycift)
"""
__version__ = "1.0.20180318"

