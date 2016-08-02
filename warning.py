#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Fetches email account information from the GleSYS email API.

Compares the account disk usage ratio to a given threshold and
notifies about account(s) that are over the thresshold, via STDOUT or
email to the account in question.

MIT license applies, see the file COPYING.

TODO:
  - Write configmaker tool
  - Add configuration setting to include all accounts in fetch.
  - Add a white list of accounts to not send warnings for.
  - Move mail subject to configuration.
  - Move mail body to configuration.
  - Move "information" string to configuration, "XX av YY (ZZ%)"
  - More verbose exception handling.

Martin Bagge <brother@bsnet.se>
Halmstad Studentkår, KAOS <kaos@karen.hh.se>
"""
from os.path import isfile
import sys
import ConfigParser
import json
import httplib2
from urllib import urlencode
import smtplib
from email.mime.text import MIMEText
from time import strftime

if isfile("config.ini") is False:
    print '''Abort: No configuration file found.
             Copy config.ini.exemple to config.ini and edit it.
             Optionally you can use ./makeconfig.py to edit the config file
             in place.'''
    sys.exit(1)

CONFIG = ConfigParser.RawConfigParser()
CONFIG.read("config.ini")

if len(CONFIG.sections()) != 4:
    print "Configuration not correct"
    sys.exit(1)


DEBUGMODE = CONFIG.getboolean("Other", "debug")
TALKATIVE = CONFIG.getboolean("Other", "verbose")

def debuginfo(outstring):
    """If debug mode is enabled in config.ini section Other a more verbose
    information flow will be used when parsing the quota info list.
    All messages will be prepended with 'DEBUG: '.

    Arguments:
        outstring (str): The informational message to be printed to STDOUT.
    """
    if DEBUGMODE is True:
        print "DEBUG: %s" % outstring

debuginfo("Fetching API settings.")
APIURL = CONFIG.get("API", "URL")
APIUSER = CONFIG.get("API", "user")
APIKEY = CONFIG.get("API", "key")

debuginfo("Fetching domain information.")
DOMAINNAME = CONFIG.get("Quota", "domainname").split(",")
MAXRATIO = CONFIG.getfloat("Quota", "ratio")

debuginfo("Fetching mail settings.")
if CONFIG.getboolean("SMTP", "enabled"):
    debuginfo("Mailing enabled.")
    SMTPENABLED = True
    SMTPSERVER = CONFIG.get("SMTP", "server")
    SMTPTLS = CONFIG.getboolean("SMTP", "TLS")
    SMTPUSER = CONFIG.get("SMTP", "user")
    SMTPPASSWORD = CONFIG.get("SMTP", "password")
    SENDER = CONFIG.get("SMTP", "sender")
else:
    debuginfo("Mailing disabled.")
    SMTPENABLED = False

debuginfo("Setting constants.")
CURRENTDATE = strftime("%Y-%m-%d")
HEADERS = {'Content-type': 'application/x-www-form-urlencoded',
           'Accept': 'application/json'}


def apirequest(target, data):
    """Takes a path target in the GleSYS API and passes the data recieved
    as a dict to using POST method. Then returns the resulting json
    response from the API call.

    Arguments:
        target (str): a target at the API - absolute.
        data  (dict): the data to post to the API.

    Returns:
        json object loaded from response content string.
        If the communication with the API fails a message is printed
        to STDOUT if debug mode is active. Will terminate with xit code 2.
    """
    try:
        httpreq = httplib2.Http()
        httpreq.add_credentials(APIUSER, APIKEY)
        _, content = httpreq.request(APIURL+target,
                                     'POST',
                                     urlencode(data),
                                     headers=HEADERS)
    except:
        debuginfo("apirequest failed. Request URL was: "+APIURL+target)
        sys.exit(2)

    return json.loads(content)


def fetchaccounts(domain):
    """Retrieves the list of email accounts available for the provided domain.
    Arguments:
        domain (str): The domain name to query from the API.

    Returns:
        The json object will be passed as return without editing.
    """
    debuginfo("Fetching email account list via API.")
    return apirequest("list", {'domainname': domain})


def fetchquota(address):
    """Retrieves the account quota information and passes the interesting
    part of the json object along to the request source.

    Arguments:
        address (str): The email account address of interest.

    Returns:
        The quota part of the json object for the response.
    """
    debuginfo("Fetching quota info for account.")
    return apirequest("quota", {'emailaccount': address})["response"]["quota"]


def sendmsg(recipient, information):
    """Sends an email message to the account provided. Uses the
    information to add some insights to the warning and indicates how
    urgent the matter is.

    Arguments:
        recipient (str): A recipient email address.
        information (str): A prepared string that will be inserted into the
                           email message. The string reads "XX of YY (ZZ%)".

    Returns:
        True if all seem to have executed correct.
        False if SMTP session did not work properly.
    """
    debuginfo("Composing mail.")
    msg = MIMEText("Hej NN\r\n\r\nDu har ganska mycket e-post lagrat nu.\r\n  "+information+"\r\nDet här meddelandet är automatiskt och skickas ut en gång i veckan. Håll dig under "+str(MAXRATIO)+"% så kommer inte dessa mail mer.\r\n\r\n-- \r\nHälsningar Kaos")
    msg['From'] = SENDER
    msg['To'] = recipient
    msg['Subject'] = "OBS! Trångt i mailkorgen - "+CURRENTDATE

    smtp = smtplib.SMTP(SMTPSERVER)
    try:
        debuginfo("Trying SMTP connection.")
        if SMTPTLS:
            smtp.starttls()
        smtp.login(SMTPUSER, SMTPPASSWORD)
        debuginfo("SMTP connection established.")
    except:
        debuginfo("Connection to mail server failed.")
        return False

    try:
        smtp.sendmail(SENDER, recipient, msg.as_string())
        smtp.close()
    except:
        debuginfo("Mail could not be sent.")
        return False
    return True


for name in DOMAINNAME:
    name = str.strip(name)
    if TALKATIVE is True or DEBUGMODE is True:
        print "Checking %s..." % name

    accountlist = fetchaccounts(name)
    for account in accountlist["response"]["list"]["emailaccounts"]:
        debuginfo("Processing "+account["emailaccount"])
        quotaobj = fetchquota(account["emailaccount"])
        used = float(quotaobj["used"]["amount"])
        allowed = float(quotaobj["total"]["max"])
        ratio = round((used / allowed) * 100, 2)
        usageinfo = str(used)+" av "+str(allowed)+" ("+str(ratio)+"%)"
        if ratio > MAXRATIO:
            if SMTPENABLED:
                sendmsg(account["emailaccount"], usageinfo)
            else:
                print "%s: %s" % (account["emailaccount"], usageinfo)
        if TALKATIVE is True or DEBUGMODE is True:
            print "%s: %s" % (account["emailaccount"], usageinfo)
