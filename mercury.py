from getpass import getpass
from contextlib import contextmanager
from email.MIMEText import MIMEText
import smtplib, requests, ConfigParser, os
from collections import defaultdict
import httplib, urllib


script_path = os.path.dirname(os.path.abspath( __file__ ))
cfg_file = os.path.join(script_path, 'mercury.cfg')


########################################################################
########################################################################
########################################################################

smtp_servers = {'gmail': ('smtp.gmail.com', 587),
              'gmx': ('smtp.gmx.com', (25, 465))}

#######################################################################

providers = defaultdict(dict)
providers['alltel'] = {'sms': 'text.wireless.alltel.com',
                       'mms': 'mms.alltel.net'}

providers['att'] = {'sms': 'txt.att.net',
                    'mms': 'mms.att.net'}

providers['att'] = {'sms': 'txt.att.net',
                    'mms': 'mms.att.net'}

providers['boost'] = {'sms': 'myboostmobile.com',
                      'mms': 'myboostmobile.com'}

providers['cricket'] = {'sms': 'sms.mycricket.com',
                        'mms': 'mms.mycricket.com'}

providers['sprint'] = {'sms': 'messaging.sprintpcs.com',
                       'mms': 'pm.sprint.com'}

providers['verizon'] = {'sms': 'vtext.com',
                        'mms': 'vzwpix.com'}

########################################################################
########################################################################
########################################################################


@contextmanager
def email_server(smtp_server, port=25, username=None, password=None):
    """
    Create an instance of smtplib.SMTP using the context manager in order
    to automatically handle the proper opening and closing of the SMTP
    server.

    with email_server('smtp.gmail.com', port=587) as server:
        server.sendmail(fromaddr, toaddrs, msg.as_string())
    """
    username = raw_input("Username: ") if username is None else username
    password = getpass() if password is None else password

    if smtp_server.lower() in smtp_servers:
        smtp_server, port = smtp_servers[smtp_server.lower()]

    if isinstance(port, int):
        ports = (port,)
    elif isinstance(port, (tuple, list)):
        ports = tuple(port)

    for p in ports:
        try:
            server = smtplib.SMTP('{}:{}'.format(smtp_server, p))
            server.ehlo();server.starttls();server.ehlo()
            server.login(username, password)
            break
        except smtplib.SMTPAuthenticationError as exc:
            server.quit()
            error = exc
            if exc.smtp_code == 454:
                continue
    else:
        raise error

    yield server
    server.quit()

def create_email(to, From=None, subject=None, message=None):
    """
    Create email using MIMEText to automate proper MIMEText creation.
    """
    if isinstance(to, str):
        toaddrs = [to]

    for t in toaddrs:
        assert '@' in t, t

    if message is None:
        message = str(raw_input("Enter Message:\n"))

    msg = MIMEText(message)
    msg['From'] = 'Python_Script' if From is None else From
    if subject is not None:
        msg['Subject'] = subject

    return toaddrs, msg


def send_message(to, message=None, From=None, subject=None, debug=False):
    """
    Send message to address(es) passed into the function using the email
    credentials provided in the .cfg file using email_server and create_email.
    """
    toaddrs, msg = create_email(to, From, subject, message)

    username = config.get('Text_Notification', 'username')
    fromaddr = config.get('Text_Notification', 'email_address')
    password = config.get('Text_Notification', 'password')
    email_provider = config.get('Text_Notification', 'email_provider')

    with email_server(email_provider, username=username, password=password) as server:
        server.set_debuglevel(debug)
        server.sendmail(fromaddr, toaddrs, msg.as_string())


def text_notification(message, subject=None):
    """
    Sends text notification using send_message to the phone number provided in
    the .cfg file using the email credentials provided in the .cfg file.
    """
    phone_address = config.get('Text_Notification', 'phone_address')
    send_message(phone_address, message=message, From=None,
                     subject=subject, debug=False)


def Pushover_Notification(message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    data = urllib.urlencode({"token": config.get('Pushover_Notification', 'app_token'),
                             "user": config.get('Pushover_Notification', 'user_key'),
                             "message": message})
    headers = { "Content-type": "application/x-www-form-urlencoded" }
    conn.request("POST", "/1/messages.json", data, headers)
    conn.getresponse()

########################################################################
########################################################################
########################################################################

def create_cfg_file():
    '''
    Create the .cfg files that store the account information used by Mercury
    to send text notifications in a Python script. Outputs 'mercury.cfg'
    '''

    config = ConfigParser.RawConfigParser()
    config.add_section('Text_Notification')

    print "CONFIG FILE GENERATOR"
    print "\tTHIS PROGRAM USES AN ACCOUNT FROM GMX OR GMAIL TO SEND TEXT MESSAGES"
    print "\tTO USA PHONE NUMBERS. THIS IS THE INITIAL SETUP TO CREATE THE"
    print "\tCONFIG FILE USED.\n"

    USERNAME = raw_input('WHAT IS YOUR USERNAME (e.g. username): ')
    config.set('Text_Notification', 'USERNAME', USERNAME)


    EMAIL_PROVIDER = raw_input('WHAT IS YOUR EMAIL PROVIDER (e.g. gmail): ')
    while EMAIL_PROVIDER not in smtp_servers:
        print EMAIL_PROVIDER + " is not currently supported.".upper()
        print "Please select on of the follows:".upper()
        for sp in smtp_servers:
            print "\t" + sp
        EMAIL_PROVIDER = raw_input('WHAT IS YOUR EMAIL PROVIDER (e.g. gmail): ')
    config.set('Text_Notification', 'EMAIL_PROVIDER', EMAIL_PROVIDER)

    if "@" in USERNAME:
        EMAIL_ADDRESS = USERNAME
    elif EMAIL_PROVIDER in  ('gmx', 'gmail'):
        EMAIL_ADDRESS = USERNAME + "@" + EMAIL_PROVIDER + ".com"
    else:
        EMAIL_ADDRESS = raw_input('WHAT IS YOUR EMAIL ADDRESS: ')

    config.set('Text_Notification', 'EMAIL_ADDRESS', EMAIL_ADDRESS)

    config.set('Text_Notification', 'PASSWORD', getpass())

    PHONE_NUMBER = raw_input('WHAT IS THE PHONE NUMBER YOU WANT TO TEXT (e.g. 8015551234): ')
    while not PHONE_NUMBER.isdigit() or len(PHONE_NUMBER) != 10:
        print PHONE_NUMBER + " is not a valid 10 digit phone number.".upper()
        PHONE_NUMBER = raw_input('WHAT IS THE PHONE NUMBER YOU WANT TO TEXT (e.g. 8015551234): ')
    config.set('Text_Notification', 'PHONE_NUMBER', PHONE_NUMBER)

    DELIVERY_METHOD = raw_input('WHAT IS THE DELIVERY METHOD YOU WANT TO USE (SMS or MMS [PREFERED]): ')
    while DELIVERY_METHOD not in ('SMS', 'MMS'):
        print DELIVERY_METHOD + " IS NOT A VALID SELECTION."
        DELIVERY_METHOD = raw_input('WHAT IS THE DELIVERY METHOD YOU WANT TO USE (SMS or MMS [PREFERED]): ')

    config.set('Text_Notification', 'DELIVERY_METHOD', DELIVERY_METHOD.lower())

    SERVICE_PROVIDER = raw_input("WHAT IS THE NUMBER'S SERVICE PROVIDER (e.g. att): ")
    while SERVICE_PROVIDER not in providers:
          print SERVICE_PROVIDER + " is not currently accepted service provide.".upper()
          print "Please select on of the follows:".upper()
          for sp in providers:
              print "\t" + sp
          SERVICE_PROVIDER = raw_input("WHAT IS THE NUMBER'S SERVICE PROVIDER (e.g. att): ")
    config.set('Text_Notification', 'SERVICE_PROVIDER', SERVICE_PROVIDER)

    PHONE_ADDRESS = '@'.join([PHONE_NUMBER, providers[SERVICE_PROVIDER][DELIVERY_METHOD.lower()]])
    config.set('Text_Notification', 'PHONE_ADDRESS', PHONE_ADDRESS)

    # Writing our configuration file to 'example.cfg'
    with open(cfg_file, 'wb') as configfile:
        config.write(configfile)

    ans = raw_input('DO YOU WANT TO SET UP YOUR PUSHOVER APP AS WELL? [Y/n]')
    if ans.lower() in ('', 'y', 'yes'):
        append_cfg_file()


def append_cfg_file():
    '''
    Append the .cfg files that store the account information used by Mercury
    to send push notifications in a Python script via Pushover. Appends 'mercury.cfg'
    '''

    config = ConfigParser.RawConfigParser()
    config.add_section('Pushover_Notification')


    APP_TOKEN = raw_input('WHAT IS YOUR APP TOKEN: ')
    while not APP_TOKEN.isalnum() or len(APP_TOKEN) != 30:
        print APP_TOKEN + " IS NOT VALID."
        print "APP TOKENS ARE 30 CHARACTER ALPHA-NUMERIC STRINGS"
        APP_TOKEN = raw_input('WHAT IS YOUR APP TOKEN: ')
    config.set('Pushover_Notification', 'APP_TOKEN', APP_TOKEN)

    USER_KEY = raw_input('WHAT IS YOUR USER KEY: ')
    while not USER_KEY.isalnum() or len(USER_KEY) != 30:
        print USER_KEY + " IS NOT VALID."
        print "USER KEYS ARE 30 CHARACTER ALPHA-NUMERIC STRINGS"
        APP_TOKEN = raw_input('WHAT IS YOUR APP TOKEN: ')
    config.set('Pushover_Notification', 'USER_KEY', USER_KEY)

    # Writing our configuration file to 'example.cfg'
    with open(cfg_file, 'ab') as configfile:
        config.write(configfile)

########################################################################
########################################################################
########################################################################

if not os.path.isfile(cfg_file):
    print "Script file is ", script_path
    print "cfg_file is ", cfg_file
    create_cfg_file()

config = ConfigParser.RawConfigParser()
config.read(cfg_file)
