import sharepy
import os
import time

# from global_utils.log_helper import LogHelper

from __app__.global_utils.log_helper import LogHelper

class SharepointHelper:
    def __init__(self, url, username=None, password=None):
        self.root_url = url[ : url.index(".com") + 4]
        self.base_url = url
        if (username is not None) and (password is not None):
            self.sharepoint_client = sharepy.connect(self.root_url, username=username, password=password)
        else:
            self.sharepoint_client = sharepy.connect(self.root_url)

    def get_list_files(self, path):
        files_info = self.sharepoint_client.get(self.base_url + "_api/Web/GetFolderByServerRelativeUrl('" + path + "')/Files").json()['d']['results']
        list_files = list(map(lambda x : "%s%s" % (self.root_url, x['ServerRelativeUrl']), files_info))
        return list_files

    def read_file(self, file_url):
        TAG = "copy-sharepoint-to-blob.function_utils.sharepoint_helper.read_file"
        if "GlobalRetryCount" in os.environ:
            try:
                try_count_remain = int(os.environ["GlobalRetryCount"])
            except:
                LogHelper.log_info(TAG, "Cannot parse GlobalRetryCount, use default value is 1")
                try_count_remain = 1
        else:
            try_count_remain = 1

        while try_count_remain > 0:
            response = self.sharepoint_client.get(file_url)
            if response.status_code == 200:
                return response.content
            else:
                # Keep retry
                try_count_remain -= 1
                time.sleep(0.5)

        # Raise error
        raise ConnectionError("%d - %s" % (response.status_code, response.reason))

    def delete_file(self, file_url):
        TAG = "copy-sharepoint-to-blob.function_utils.sharepoint_helper.delete_file"
        if "GlobalRetryCount" in os.environ:
            try:
                try_count_remain = int(os.environ["GlobalRetryCount"])
            except:
                LogHelper.log_info(TAG, "Cannot parse GlobalRetryCount, use default value is 1")
                try_count_remain = 1
        else:
            try_count_remain = 1

        while try_count_remain > 0:
            response = self.sharepoint_client.delete(file_url)
            if response.status_code == 204:
                return response.content
            else:
                # Keep retry
                try_count_remain -= 1
                time.sleep(0.5)

        # Raise error
        raise ConnectionError("%d - %s" % (response.status_code, response.reason))



