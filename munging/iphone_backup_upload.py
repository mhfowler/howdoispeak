import os, json, re, sqlite3, datetime, time, random, urllib2
from munging.common import PROJECT_PATH, SECRETS
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from subprocess import Popen, PIPE

HOME_DIR = os.path.expanduser("~")
MAC_IPHONE_BACKUP_DIR_RELATIVE = "/Library/Application Support/MobileSync/Backup/"
MAC_IPHONE_BACKUP_DIR = HOME_DIR + MAC_IPHONE_BACKUP_DIR_RELATIVE
MAC_SMS_BACKUP_FILE = "3d0d7e5fb2ce288813306e4d4636395e047a3d28"
MAC_CONTACTS_BACKUP_FILE = "31bb7ba8914766d4ba40d6dfb6113c8b614be442"


class ParseBackupDB:
    # data we will populate
    handle_id_to_phone_number = {}
    sms_dict = {
            "user_meta":{},
            "texts":[]
        }
    phone_number_to_name = {}
    num_unknown = 0
    MAC_SMS_BACKUP_PATH = ""
    MAC_CONTACTS_BACKUP_PATH = ""
    MAC_BACKUP_PATH = ""

    def stripPhoneNumber(self,phone_number):
        phone_number = re.sub('[^0-9]', '', phone_number)
        if len(phone_number) == 11 and phone_number[0] == "1":
            phone_number = phone_number[1:]
        return phone_number


    def populateHandleIDToPhoneNumber(self):

           # make db connection
        db_path=self.MAC_SMS_BACKUP_PATH
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # read data from sqlite and put into dictionary
        read_query = "select message.handle_id as handle_id,handle.id as phone_number from message join handle on message.handle_id=handle.ROWID"
        for row in c.execute(read_query):
            handle_id, phone_number = row
            # strip phone number of everything but numbers
            phone_number = self.stripPhoneNumber(phone_number)
            self.handle_id_to_phone_number[handle_id] = phone_number

        # close connection
        conn.close()


    def populatePhoneNumberToName(self):

        # make db connection
        db_path=self.MAC_CONTACTS_BACKUP_PATH
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # read data from sqlite and put into dictionary
        read_query = "SELECT ABMultiValue.value as phone_number, ABPerson.first as first_name, ABPerson.last as last_name" \
                     " FROM ABMultiValue JOIN ABPerson on ABMultiValue.record_id=ABPerson.ROWID WHERE ABMultiValue.property=3"
        for row in c.execute(read_query):
            phone_number,first_name,last_name = row
            # strip phone number of everything but numbers
            phone_number = self.stripPhoneNumber(phone_number)
            # create full name
            if first_name and last_name:
                full_name = first_name + " " + last_name
            elif first_name:
                full_name = first_name
            else:
                full_name = last_name
            self.phone_number_to_name[phone_number] = full_name

        # close connection
        conn.close()


    def convertBackupDBtoDictAfterPopulation(self):

        # make db connection
        db_path=self.MAC_SMS_BACKUP_PATH
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # read data from sqlite and put into dictionary
        read_query = "SELECT `text`,`handle_id`,`is_from_me`,`date` FROM `message`"
        for row in c.execute(read_query):
            text,handle_id,is_from_me,date = row

            # try to get name from handle_id
            phone_number = self.handle_id_to_phone_number.get(handle_id)
            if phone_number:
                name = self.phone_number_to_name.get(phone_number)
                if not name: name=phone_number
            else:
                name= "unknown" + str(handle_id)

            # assign name to appropriate person
            from_user = "me"
            to_user = "me"
            if is_from_me == 1:
                to_user = name
            else:
                from_user = name
            text_data = {
                "from_name":from_user,
                "to_name":to_user,
                "text_message":text,
                "data":date
            }
            self.sms_dict["texts"].append(text_data)


        # close connection
        conn.close()

    # determines which folder in the mobile backup directory actually has the latest backups
    def determineBackupDirPath(self):
        all_backups_dir = MAC_IPHONE_BACKUP_DIR
        latest_backup_dir = None
        latest_backup_time = 0
        for (dirpath, dirnames, filenames) in os.walk(all_backups_dir):
            for d in dirnames:
                d_path = os.path.join(dirpath, d)
                # check if it contains the correct files
                files_in_dir = os.listdir(d_path)
                if MAC_SMS_BACKUP_FILE in files_in_dir and MAC_CONTACTS_BACKUP_FILE in files_in_dir:
                    seconds = os.path.getmtime(d_path)
                    # check if it is the latest
                    if seconds > latest_backup_time:
                        latest_backup_time = seconds
                        latest_backup_dir = d_path
        self.MAC_BACKUP_PATH = latest_backup_dir
        self.MAC_SMS_BACKUP_PATH = os.path.join(latest_backup_dir, MAC_SMS_BACKUP_FILE)
        self.MAC_CONTACTS_BACKUP_PATH = os.path.join(latest_backup_dir, MAC_CONTACTS_BACKUP_FILE)


    def convertBackupDBToDict(self):
        self.determineBackupDirPath()
        self.populateHandleIDToPhoneNumber()
        self.populatePhoneNumberToName()
        self.convertBackupDBtoDictAfterPopulation()


    def writeSMSDictToFile(self, out_file_path):
        out_file = open(out_file_path, "w")
        to_write = json.dumps(self.sms_dict)
        out_file.write(to_write)


    def uploadToS3(self):
        aws_access_key_id = SECRETS["AWS_ACCESS_KEY_ID"]
        aws_secret_access_key = SECRETS["AWS_SECRET_ACCESS_KEY"]
        conn = S3Connection(aws_access_key_id, aws_secret_access_key)

        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        random_appendage = str(random.randint(0,10000000000))
        st = st + " ~" + random_appendage + "~ "

        b = conn.get_bucket('howdoispeak')

        k = Key(b)
        k.key = st
        to_write = json.dumps(self.sms_dict)
        k.set_contents_from_string(to_write)


    def loadJSONFromFile(self, file_path):
        f = open(file_path, "r")
        self.sms_dict = json.loads(f.read())


    def getPublicIPAddress(self):
        self.sms_dict["user_meta"]["ip_address"] = urllib2.urlopen('http://ip.42.pl/raw').read()

    def getUserName(self):
        scpt = '''
        on run {}
        display dialog "Please enter your name or email so we know who to send the results of your SMS analysis to: " default answer ""
            set full_name to text returned of result
            return full_name
        end run
        '''
        full_name = self.runAppleScript(scpt)
        full_name = full_name.replace("\n","")
        self.sms_dict["user_meta"]["user_name"] = full_name

    def checkSuccess(self):
        text_messages = self.sms_dict["texts"]
        return len(text_messages) > 5

    def runAppleScript(self, scpt):
        args = []
        p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(scpt)
        return stdout

    def alertMessage(self, message):
        scpt = '\non run {}' + \
        '\ndisplay notification "' + message + '"' +\
        '\nend run\n'
        self.runAppleScript(scpt)

def mainFun():
    pdb = ParseBackupDB()
    pdb.getUserName()
    pdb.alertMessage("It may take a couple minutes to process your SMS Data. Please wait for a notification...")
    pdb.convertBackupDBToDict()
    pdb.getPublicIPAddress()
    if pdb.checkSuccess():
        try:
            pdb.uploadToS3()
            pdb.alertMessage("Successfully transferred SMS data. Thanks for participating!")
        except:
            pdb.alertMessage("Oops, there was an error... please send us an email and let us know.")
    else:
        pdb.alertMessage("Oops, there was an error processing SMS data... please send us an email and let us know.")



if __name__ == "__main__":
    mainFun()



