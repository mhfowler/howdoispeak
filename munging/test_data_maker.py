__author__ = 'maxfowler'
import os, json, re, sqlite3, datetime, time, random, urllib2
import datetime
from common import PROJECT_PATH, SECRETS
from boto.s3.connection import S3Connection
from boto.s3.key import Key

raw_file_dir = "/Users/maxfowler/Desktop/cs/howdoispeak/dist"
raw_file_path = raw_file_dir + "/test.txt"
with open(raw_file_path, "r") as test_f:
    raw_data = json.loads(test_f.read())
    conversations = raw_data["conversations"]
    counts = raw_data["counts"]
    conversation_keys = list(conversations.keys())
    first_key = conversation_keys[0]
    single_conversation = {first_key: conversations[first_key]}
    # truncate counts as well
    counts_keys = list(counts.keys())
    first_count_key = counts_keys[0]
    single_count = {first_count_key: counts[first_count_key]}

    raw_data["counts"] = single_count
    raw_data["conversations"] = single_conversation
    truncated_file_path = raw_file_dir + "/truncated.txt"
    to_write = json.dumps(raw_data)
    with open(truncated_file_path, "w") as truncated_f:
        truncated_f.write(to_write)

    # put truncate file in s3
    aws_access_key_id = SECRETS["AWS_ACCESS_KEY_ID"]
    aws_secret_access_key = SECRETS["AWS_SECRET_ACCESS_KEY"]
    conn = S3Connection(aws_access_key_id, aws_secret_access_key)

    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d|%H:%M:%S')
    random_appendage = str(random.randint(0,10000000000))
    st = st + "|~" + random_appendage + "~"

    user_name = "truncated"
    folder = "raw/"
    st = st + "|" + user_name
    st = folder + st

    b = conn.get_bucket('howdoispeak')

    k = Key(b)
    k.key = st

    # push contents to s3
    k.set_contents_from_string(to_write)



