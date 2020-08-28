import os
import sys
import azure.functions as func

# from copy_sharepoint_to_blob.function_utils.copy_helper import CopyHelper
# from global_utils.log_helper import LogHelper

from __app__.copy_sharepoint_to_blob.function_utils.copy_helper import CopyHelper
from __app__.global_utils.log_helper import LogHelper

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)

def main(req: func.HttpRequest) -> func.HttpResponse:
    TAG = "copy_sharepoint_to_blob.__init__.main"
    LogHelper.log_info(TAG, 'Python HTTP trigger function processed a request.')

    request_params = req.get_json()
    sharepoint_path = request_params["sharepoint_path"]
    blob_path = request_params["blob_path"]

    if "prefix" in request_params:
        prefix = request_params["prefix"]
    else:
        prefix = None

    if "suffix" in request_params:
        suffix = request_params["suffix"]
    else:
        suffix = None

    copy_helper = CopyHelper()

    sharepoint_url = os.environ["SharepointBaseUrl"]
    username = os.environ["SharepointUsername"]
    password = os.environ["SharepointPassword"]
    copy_helper.connect_to_sharepoint(sharepoint_url, username, password)

    blob_account = os.environ["BlobStorageAccount"]
    blob_key = os.environ["BlobStorageKey"]
    copy_helper.connect_to_blob(blob_account, blob_key)

    copied_list = copy_helper.copy_from_sharepoint_folder_to_blob(sharepoint_path, blob_path, prefix, suffix)
    message_str = "%d files are copied: %s" % (len(copied_list), ", ".join(copied_list))
    return_json = "{ \"message\" : \"%s\" }" % message_str
    return func.HttpResponse(return_json, status_code=200)
