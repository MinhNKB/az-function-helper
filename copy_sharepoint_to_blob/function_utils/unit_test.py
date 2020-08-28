import logging
import os

from copy_sharepoint_to_blob.function_utils.copy_helper import CopyHelper

if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    copy_helper = CopyHelper()

    url = "https://biasaigon.sharepoint.com/sites/SabecoBIDev/"
    username = "jadev@sabeco.com.vn"
    password = "JA@#@2020Jul"
    copy_helper.connect_to_sharepoint(url, username, password)

    blob_account = "sbcstorageacount"
    blob_key = "O8u92YnD90jsl/46QMSXj0iR+2wac6TKzuXJ76roZM8bHq5z+P3+dbFUDTjbGiJMks01yk31dFKsgQFyeMFLbQ=="
    copy_helper.connect_to_blob(blob_account, blob_key)

    sharepoint_path = "Shared Documents/Upload/RLS"
    blob_path = "test/minh"
    copy_helper.copy_from_sharepoint_folder_to_blob(sharepoint_path, blob_path, "20200727", "JA")