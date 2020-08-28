from io import BytesIO

# from global_utils.sharepoint_helper import SharepointHelper
# from global_utils.blob_helper import BlobHelper
# from global_utils.log_helper import LogHelper

from __app__.global_utils.sharepoint_helper import SharepointHelper
from __app__.global_utils.blob_helper import BlobHelper
from __app__.global_utils.log_helper import LogHelper


class CopyHelper:
    def __init__(self):
        self.sharepoint_helper = None
        self.blob_helper = None

    def connect_to_sharepoint(self, url, username, password):
        self.sharepoint_helper = SharepointHelper(url, username, password)

    def connect_to_blob(self, blob_account, blob_key):
        self.blob_helper = BlobHelper(blob_account, blob_key)

    def copy_from_sharepoint_folder_to_blob(self, sharepoint_folder, blob_path, prefix = None, suffix = None):
        TAG = "copy-sharepoint-to-blob.function_utils.copy_helper.copy_from_sharepoint_folder_to_blob"
        if self.sharepoint_helper is None:
            raise ConnectionError("Connection to Sharepoint was not established")
        if self.blob_helper is None:
            raise ConnectionError("Connection to Blob was not established")

        files_list = self.sharepoint_helper.get_list_files(sharepoint_folder)

        blob_path = blob_path.strip("/")
        container = blob_path[ : blob_path.index("/")]
        remain_path = blob_path[blob_path.index("/") + 1 : ]

        copied_list = []
        for file_url in files_list:
            LogHelper.log_info(TAG, "Copying %s" % file_url)
            file_name = file_url[file_url.rindex("/") + 1 : file_url.rindex(".")]
            extension = file_url[file_url.rindex(".") : ]

            if prefix is not None:
                file_name = prefix + "_" + file_name
            if suffix is not None:
                file_name = file_name + "_" + suffix
            file_path = remain_path + "/" + file_name + extension

            bytes = self.sharepoint_helper.read_file(file_url)

            self.blob_helper.upload_data(BytesIO(bytes), container, file_path)
            
            copied_list.append(file_name)
            self.sharepoint_helper.delete_file(file_url)
        return copied_list