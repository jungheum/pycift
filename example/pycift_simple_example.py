"""pycift_simple_example

    * Description
        A simple example of 'pycift'

    * Author
        Hyunji Chung  <localchung@gmail.com>
        Jungheum Park <junghmi@gmail.com>
"""

import os
import json
from pycift.common_defines import *
from pycift.utility.pt_utils import PtUtils
from pycift.acquisition.amazon_alexa import AmazonAlexaInterface
from pycift.acquisition.google_assistant import GoogleAssistantInterface


def set_inputs(cift, param):
    if param.get(INPUT_CLIENT) is not None:
        target = param.get(INPUT_CLIENT)
        if target.get(INPUT_CLIENT_ANDROID) is not None:
            for path in target.get(INPUT_CLIENT_ANDROID):
                cift.add_input(CIFTOperation.COMPANION_APP_ANDROID, path)

        if target.get(INPUT_CLIENT_IOS) is not None:
            for path in target.get(INPUT_CLIENT_IOS):
                cift.add_input(CIFTOperation.COMPANION_APP_IOS, path)

        if target.get(INPUT_CLIENT_CHROMIUM) is not None:
            for path in target.get(INPUT_CLIENT_CHROMIUM):
                cift.add_input(CIFTOperation.COMPANION_BROWSER_CHROME, path)

    if param.get(INPUT_CLOUD) is not None:
        target = param.get(INPUT_CLOUD)
        if target.get(INPUT_CLOUD_CRED_IDPW) is not None:
            for idpw in target.get(INPUT_CLOUD_CRED_IDPW):
                if idpw.get("id") is not None and idpw.get("pw") is not None:
                    cift.add_input(
                        CIFTOperation.CLOUD, idpw.get("id"), idpw.get("pw")
                    )

        if target.get(INPUT_CLOUD_CRED_COOKIE) is not None:
            for cookie in target.get(INPUT_CLOUD_CRED_COOKIE):
                if cookie is not None and cookie != {}:
                    cift.add_input(CIFTOperation.CLOUD, cookie)


def main():
    # Read user inputs
    input_file = "pycift_input_1.json"  # NEED TO BE EDITED using pycift_input_template.json
    data = open(input_file).read()
    try:
        data = json.loads(data)
    except ValueError:
        print("Invalid input file")
        return

    # Simple validation for the input file
    if data.get(CIFT_AMAZON_ALEXA) is None and data.get(CIFT_GOOGLE_ASSISTANT) is None:
        return

    # ------------------------------------------------------------------
    # Generate a unique name for creating a result directory
    base = "CIFT_RESULT"
    if CIFT_DEBUG is True:
        base_dir = "./(DEBUG)_{}".format(base)
    else:
        d, t = PtUtils.get_current_date_and_time()
        base_dir = "./({}_{})_{}".format(d, t.replace(":", "."), base)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Process inputs relating to Amazon Alexa
    module = data.get(CIFT_AMAZON_ALEXA)
    if module is not None:
        if module.get(INPUT_ENABLED) is True:
            # Create an interface for processing Amazon Alexa related inputs
            cift = AmazonAlexaInterface()
            cift.basic_config(
                path_base_dir=base_dir,
                browser_driver=CIFTBrowserDrive.CHROME,
                options=[CIFTOption.DOWNLOAD_VOICE_DATA]
            )

            set_inputs(cift, module)

            cift.run()

            cift.close()
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Process inputs relating to Google Assistant
    module = data.get(CIFT_GOOGLE_ASSISTANT)
    if module is not None:
        if module.get(INPUT_ENABLED) is True:
            # Create an interface for processing Google Assistant related inputs
            cift = GoogleAssistantInterface()
            cift.basic_config(
                path_base_dir=base_dir,
                browser_driver=CIFTBrowserDrive.CHROME,
                options=[CIFTOption.DOWNLOAD_VOICE_DATA]
            )

            set_inputs(cift, module)

            cift.run()

            cift.close()
    # ------------------------------------------------------------------

    filename = "last_progress_log.txt"
    if os.path.exists(filename) is True:
        new_path = "{}\\{}".format(base_dir, filename)
        PtUtils.copy_file(filename, new_path)
    return


if __name__ == "__main__":
    main()

