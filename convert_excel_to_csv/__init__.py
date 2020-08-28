import logging
import sys
import azure.functions as func
import os

# from convert_excel_to_csv.function_utils.convert_helper import ConvertHelper
# from global_utils.log_helper import LogHelper

from __app__.convert_excel_to_csv.function_utils.convert_helper import ConvertHelper
from __app__.global_utils.log_helper import LogHelper

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

def main(req: func.HttpRequest) -> func.HttpResponse:
    TAG = "convert_excel_to_csv.__init__.main"
    LogHelper.log_info(TAG, 'Python HTTP trigger function processed a request.')

    request_params = req.get_json()

    convert_helper = ConvertHelper()
    blob_account = os.environ["BlobStorageAccount"]
    blob_key = os.environ["BlobStorageKey"]
    convert_helper.connect_to_blob(blob_account, blob_key)

    convert_helper.convert_excel_to_csv(request_params)
    blob_name = request_params['blob_input']['blobname']
    message_string = "Convert blob %s successfully" % blob_name
    return_json = "{ \"message\" : \"%s\" }" % message_string
    return func.HttpResponse(return_json, status_code=200)