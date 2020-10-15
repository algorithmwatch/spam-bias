from imapclient import IMAPClient
from peewee import *
import email, datetime, os
from inboxes import inboxes

if 'CLEARDB_DATABASE_URL' not in os.environ:
    from playhouse.sqlite_ext import SqliteExtDatabase

if 'CLEARDB_DATABASE_URL' in os.environ:
    url = urlparse.urlparse(os.environ['CLEARDB_DATABASE_URL'])
    db = peewee.MySQLDatabase(url.path[1:], host=url.hostname, user=url.username, passwd=url.password)
else:
    db = SqliteExtDatabase('/home/nkb/code/spam-bias/emails.db')

class Email(Model):
    subject = CharField()
    sender = CharField()
    date = DateTimeField(default=datetime.datetime.now)
    body = CharField()
    folder = CharField()
    account = CharField()

    class Meta:
        database = db

db.connect()

db.create_tables([Email], safe = True)

hosts = {
    "Gmail": {
        "url": "imap.gmail.com",
        "spam": "[Gmail]/Spam",
        "inbox": "INBOX"
    },
    "gmx": {
        "url": "imap.gmx.net",
        "spam": "Spamverdacht",
        "inbox": "INBOX"
    },
    "hotmail": {
        "url": "outlook.office365.com",
        "spam": "Junk",
        "inbox": "Inbox"
    },
    "yahoo": {
        "url": "imap.mail.yahoo.com",
        "spam": "Bulk Mail",
        "inbox": "Inbox"
    },
    "laposte": {
        "url": "imap.laposte.net",
        "spam": "INBOX/QUARANTAINE",
        "inbox": "INBOX"
    }
}

def get_mail(user, server, folder):
    print('\033[94m', user, folder, '\033[0m')
    select_info = server.select_folder(folder)
    messages = server.search('UNSEEN')
    for uid, message_data in server.fetch(messages, 'RFC822').items():
        email_message = email.message_from_bytes(message_data[b'RFC822'])
        print("New message from: ", email_message.get('From'))
        for part in email_message.walk():
            if(part.get_content_type() == "text/html"):
            	body = part
        Email( subject=email_message.get('Subject')
             , sender=email_message.get('From')
             , date=email_message.get('Date')
             , body=body
             , folder=folder
             , account=user).save()

for account in inboxes:
    host = hosts[account["host"]]["url"]
    user = account["u"]
    pwd  = account["p"]
    spam_folder = hosts[account["host"]]["spam"]
    mail_folder = hosts[account["host"]]["inbox"]

    server = IMAPClient(host, use_uid=True)
    server.login(user, pwd)

    # For new services, uncomment this line to get the name of the folders
    #print(server.list_folders())

    get_mail(user, server, mail_folder)
    get_mail(user, server, spam_folder)

