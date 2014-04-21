import json, datetime, random
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import os, json

class TextData():

    def __init__(self):

        self.text_data = []
        self.unfiltered_text_data = self.text_data
        self.users_data = []
        self.usernames = set([])
        self.num_unknown = 0

        self.PROJECT_PATH =  os.path.abspath(os.path.dirname(__file__))
        secrets_file_path = os.path.join(self.PROJECT_PATH, "secrets.json")
        secrets_json = open(secrets_file_path).read()
        self.SECRETS = json.loads(secrets_json)
        self.aws_access_key_id = self.SECRETS["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = self.SECRETS["AWS_SECRET_ACCESS_KEY"]

    def getUnknownID(self):
        self.num_unknown += 1
        return self.num_unknown

    def strEncode(self, the_string):
        if the_string:
            return the_string.encode(encoding='UTF-8',errors='strict')
        else:
            return ""

    def convertTimeToPython(self, string_time):
        return datetime.datetime.now()  # TODO

    def loadJSON(self, json_string):
        f_data = json.loads(json_string)
        user_name = f_data["user_meta"].get("user_name")
        if not user_name:
            user_name = "unknown" + str(self.num_unknown)
        else:
            if user_name in self.usernames: user_name += str(self.num_unknown)
        user_data = {
            "user_name":user_name,
            "ip_address":f_data["user_meta"].get("ip_address")
        }
        self.usernames.add(user_name)
        self.users_data.append(user_data)
        for text in f_data["texts"]:
            if text["from_name"] == "me":
                text["from_name"] = user_name
            else:
                text["to_name"] = user_name
            text["date"] = self.convertTimeToPython(text.get("date"))
            self.text_data.append(text)

    def getTextData(self):
        return self.text_data

    def filterTextDataByTime(self, start_time, end_time):
        filtered_text_data = []
        for text in self.text_data:
            text_time = text["date"]
            if start_time and end_time:
                if text_time > start_time and text_time < end_time:
                    filtered_text_data.append(text)
            elif start_time:
                if text_time > start_time:
                    filtered_text_data.append(text)
            elif end_time:
                if text_time < end_time:
                    filtered_text_data.append(text)
            else:
                filtered_text_data.append(text)
        self.text_data = filtered_text_data

    def filterDataByUsers(self, to_users=None, from_users=None):
        filtered_text_data = []
        for text in self.text_data:
            to_name = text["to_name"]
            from_name = text["from_name"]
            if to_users and from_users:
                if to_name in to_users and from_name in from_users:
                    filtered_text_data.append(text)
            elif to_users:
                if to_name in to_users:
                    filtered_text_data.append(text)
            elif from_users:
                if from_name in from_users:
                    filtered_text_data.append(text)
            else:
                filtered_text_data.append(text)
        self.text_data = filtered_text_data

    def removeFilters(self):
        self.text_data = self.unfiltered_text_data

    def loadFromJSONFiles(self, file_paths):
        for file_path in file_paths:
            f = open(file_path, "r")
            self.loadJSON(f.read())

    def loadFromS3Keys(self, s3_keys):
        for k in s3_keys:
            print k.name
            json_string = k.get_contents_as_string()
            self.loadJSON(json_string)

    def getS3Keys(self, num=0):
        conn = S3Connection(self.aws_access_key_id, self.aws_secret_access_key)
        bucket = conn.get_bucket('howdoispeak')
        keys = bucket.list()
        keys_list = []
        for key in keys:
            keys_list.append(key)
        if num:
            keys_list = random.sample(keys_list, num)
        return keys_list

    def getTextBlob(self):
        text_blob = ""
        for text in self.text_data:
            text_blob += " " + self.strEncode(text.get("text_message"))
        return text_blob


if __name__ == "__main__":
    td = TextData()
    s3_keys = td.getS3Keys(1)
    td.loadFromS3Keys(s3_keys)
    print td.getTextBlob()



