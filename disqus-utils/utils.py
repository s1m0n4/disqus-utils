# -*- coding: utf-8 -*-
'''
   Created on Dec 9, 2016
   @author: s1m0n4
   @copyright: 2016 s1m0n4
'''
import os
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

def read_file(f):
    '''
    @return: the file contents if the file exists, otherwise None.
    '''
    result = None
    if os.path.exists(f):
        if os.path.isfile(f):
            with open(f, 'r') as fo:
                result = fo.read()
    return result


def write_file(ifile, contents, mode='w'):
    '''
    Opens a file and writes the contents
    '''
    with open(ifile, mode) as f:
        f.write(contents)
        f.flush()

    return True


def send_email(sender, recipients, subject, text, smtp, files=[], port=465, user=None, password=None):
    # Create a text/plain message
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ",".join(recipients)
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(text))
    
    for f in files:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)
        
    smtp_server = None
    try:
        smtp_server = smtplib.SMTP_SSL(smtp, port=port)
        smtp_server.set_debuglevel(True)
        smtp_server.ehlo()
        if user:
            smtp_server.login(user, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    finally:
        if smtp_server:
            smtp_server.quit()
    
    return True


def log_config_error_and_exit(missing_setting, logger):
    logger.error("Missing required config setting: %s" % missing_setting)
    exit(2)


def verify_required_setting(config_dict, required_settings_list, logger):
    for required_setting in required_settings_list:
        setting = config_dict.get(required_setting)
        if not setting:
            log_config_error_and_exit(required_setting, logger)
        if len(setting.strip()) == 0:
            log_config_error_and_exit(required_setting, logger)
