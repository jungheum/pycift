# [Under Construction - expected until Mar 18, 2018]

# pycift

A Python implementation of CIFT (Cloud-based IoT Forensic Toolkit)


## Installation

Tested Python versions: Python 3.5

Install the latest version:

	$ git clone https://bitbucket.org/cift/pycift
	$ cd pycift
	$ python setup.py install


## Examples

### (1) amazon_alexa.client.android_app

* Amazon Alexa app-related data from smartphone images of DFRWS 2018 Challenge

#### Set user-inputs (Refer to [pycift_input_template.json](\example\pycift_input_template.json))

pycift_input_example_1.json

```
#!json
{
  {
  "cift_amazon_alexa": {
    "enabled": true,
    "client": {
      "android_app": [
        "D:/artifacts/android/dfrws_challenge_2018/002-BettyNote2Black/com.amazon.dee.app/",
        "D:/artifacts/android/dfrws_challenge_2018/003-SimonNote2White/com.amazon.dee.app/"
      ]
    }
  }
}
```

#### Code snippets of (\example\pycift_simple_example.py)

Import `pycift` modules:

```
#!python
from pycift.common_defines import *
from pycift.acquisition.amazon_alexa import AmazonAlexaInterface
from pycift.acquisition.google_assistant import GoogleAssistantInterface 		
```

Load user-inputs:

    input_file = "pycift_input.json"
    data = json.loads(open(input_file).read())

Create an interface for processing each IVA ecosystem-related inputs:

    cift = AmazonAlexaInterface()
    # cift = GoogleAssistantInterface()  # for Google Assistant-related operations

Configure options:

    cift.basic_config(
        path_base_dir=base_dir,                   # Output path
        browser_driver=CIFTBrowserDrive.CHROME,   # Browser driver
        options=[CIFTOption.DOWNLOAD_VOICE_DATA]  # For downloading voice data from cloud side
    )

Set user-inputs:

    # Processing JSON-formatted user-inputs ("pycift_input.json")
    # ...(skip)...

    # Corpus creators can utilize add_input() to set each input as follows:
    # ...(skip)...

Run `pycift` modules:

    cift.run()

#### Results

The results were created on the log directory (\example\\(2018-XX-XX_YY.YY.YY)_CIFT_RESULT\\)

* Evidence_Library


## License

Apache License 2.0
