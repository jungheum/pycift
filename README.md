pycift
================================

> A Python implementation of **CIFT** (Cloud-based IoT Forensic Toolkit)
> 
> See [Description and version history](https://bitbucket.org/cift/pycift/src/master/pycift/__init__.py?fileviewer=file-view-default)
>
> CIFT wiki is under construction for providing more information

- - -

## Installation

Tested Python versions: Python 3.5

Tested Operating Systems: Windows 10 (Linux and macOS will be tested soon)

Install the latest version:

	$ git clone https://bitbucket.org/cift/pycift
	$ cd pycift
	$ python setup.py install

- - -

## Exampe 1. amazon_alexa.client.android_app

Amazon Alexa app-related data from smartphone images of DFRWS 2018 Challenge

#### Set user-inputs (cf. [pycift_input_template.json](https://bitbucket.org/cift/pycift/src/master/example/pycift_input_template.json?fileviewer=file-view-default))

pycift_input_example_1.json

```
#!json
{
  {
  "cift_amazon_alexa": {
    "enabled": true,
    "client": {
      "android_app": [
        "D:/client_centric_artifacts/android/dfrws_challenge_2018/002-BettyNote2Black/com.amazon.dee.app/",
        "D:/client_centric_artifacts/android/dfrws_challenge_2018/003-SimonNote2White/com.amazon.dee.app/"
      ]
    }
  }
}
```

#### Code snippets of [pycift_simple_example.py](https://bitbucket.org/cift/pycift/src/master/example/pycift_simple_example.py?fileviewer=file-view-default))

Import `pycift` modules:

```
#!python
from pycift.common_defines import *
from pycift.acquisition.amazon_alexa import AmazonAlexaInterface
from pycift.acquisition.google_assistant import GoogleAssistantInterface 		
```

Create an interface for processing each IoT ecosystem-related inputs:
```
#!python
cift = AmazonAlexaInterface()        # for Amazon Alexa-related operations
# cift = GoogleAssistantInterface()  # for Google Assistant-related operations
```

Configure options:

```
#!python
cift.basic_config(
    path_base_dir=base_dir,                   # Output path
    browser_driver=CIFTBrowserDrive.CHROME,   # Browser driver
    options=[CIFTOption.DOWNLOAD_VOICE_DATA]  # For downloading voice data from cloud side
)
```

Set user-inputs:

```
#!python
# Processing JSON-formatted user-inputs ("pycift_input_example_1.json")
# ...(skip)...

# Corpus creators can utilize add_input() to set each input as follows:
cift.add_input(CIFTOperation.CLOUD, idpw.get("id"), idpw.get("pw"))
cift.add_input(CIFTOperation.CLOUD, cookie)
cift.add_input(CIFTOperation.COMPANION_APP_ANDROID, path)
cift.add_input(CIFTOperation.COMPANION_APP_IOS, path)
cift.add_input(CIFTOperation.COMPANION_BROWSER_CHROME, path)
```

Run `pycift` modules:

```
#!python
cift.run()
```

#### Results

The results were created on an output directory ([CIFT_RESULT](https://bitbucket.org/cift/pycift/src/master/example/(EXAMPLE-1)_CIFT_RESULT_DC2018/))

+ cift_amazon_alexa.db [257 KB]
    * cf. [Alexa DB schema](https://bitbucket.org/cift/pycift/src/master/pycift/report/db_models_amazon_alexa.py) 
+ Evidence_Library:
    * AmazonAlexaClient [0.99 MB]
        1. 342 JSON files
        2. 6 SQLite DB files
        3. 2 event log files        
+ last_progress_log.txt [809 KB]
    * Progress logs

- - -

## Exampe 2. amazon_alexa.cloud.credential_cookie

Soon

- - -

## Exampe 3. google_assistant.cloud.credential_idpw

Soon

- - -

## License

Apache License 2.0

