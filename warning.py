#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Fetches email account information from the GleSYS email API.

Compares the account disk usage ratio to a given threshold and
notifies about account(s) that are over the thresshold, via STDOUT or
email to the account in question.

MIT license applies, see the file COPYING.

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

# TODO: Write the tool.
if isfile("config.ini") is False:
    print '''Abort: No configuration file found.
             Copy config.ini.exemple to config.ini and edit it.
             Optionally you can use ./makeconfig.py to edit the config file
             in place.'''
    sys.exit(1)

cfg = ConfigParser.RawConfigParser()
cfg.read("config.ini")

if len(cfg.sections()) != 3:
    print "Configuration not correct"
    sys.exit(1)

apiurl = cfg.get("API", "URL")
apiuser = cfg.get("API", "user")
apikey = cfg.get("API", "key")

domainname = cfg.get("Quota", "domainname").split(",")
# TODO: Add setting for showing all - not just "violators".
maxratio = cfg.getfloat("Quota", "ratio")

if cfg.getboolean("SMTP", "enabled"):
    smtpenabled = True
    smtpserver = cfg.get("SMTP", "server")
    smtptls = cfg.getboolean("SMTP", "TLS")
    smtpuser = cfg.get("SMTP", "user")
    smtppassword = cfg.get("SMTP", "password")
    sender = cfg.get("SMTP", "sender")
else:
    smtpenabled = False

currentdate = strftime("%Y-%m-%d")
headers = {'Content-type': 'application/x-www-form-urlencoded',
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
        to STDOUT and a exit code 2 generated.
    """
    try:
        h = httplib2.Http()
        h.add_credentials(apiuser, apikey)
        resp, content = h.request(apiurl+target,
                                  'POST',
                                  urlencode(data),
                                  headers=headers)
    except:
        print "No connection"
        sys.exit(2)

    return json.loads(content)


def fetchaccounts(domain):
    """Retrieves the list of email accounts available for the provided domain.
    Arguments:
        domain (str): The domain name to query from the API.

    Returns:
        The json object will be passed as return without editing.
    """
    return apirequest("list", {'domainname': domain})


def fetchquota(address):
    """Retrieves the account quota information and passes the interesting
    part of the json object along to the request source.

    Arguments:
        address (str): The email account address of interest.

    Returns:
        The quota part of the json object for the response.
    """
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
    # TODO: Add list of "whitelisted" addresses.
    # TODO: Move to config
    msg = MIMEText("Hej NN\r\n\r\nDu har ganska mycket e-post lagrat nu.\r\n  "+information+"\r\nDet här meddelandet är automatiskt och skickas ut en gång i veckan. Håll dig under "+str(maxratio)+"% så kommer inte dessa mail mer.\r\n\r\n-- \r\nHälsningar Kaos")
    msg['From'] = sender
    msg['To'] = recipient
    # TODO: Move to config.
    msg['Subject'] = "OBS! Trångt i mailkorgen - "+currentdate

    smtp = smtplib.SMTP(smtpserver)
    try:
        if smtptls:
            smtp.starttls()
        smtp.login(smtpuser, smtppassword)
    except:
        print "SMTP login failed"
        return -1

    smtp.sendmail(sender, recipient, msg.as_string())
    smtp.close()


for name in domainname:
    if smtpenabled is False:
        print "Checking %s..." % name

    accountlist = fetchaccounts(name)
    for account in accountlist["response"]["list"]["emailaccounts"]:
        quotaobj = fetchquota(account["emailaccount"])
        used = float(quotaobj["used"]["amount"])
        allowed = float(quotaobj["total"]["max"])
        ratio = round((used / allowed) * 100, 2)
        if ratio > maxratio:
            usageinfo = str(used)+" av "+str(allowed)+" ("+str(ratio)+"%)"
            if smtpenabled:
                sendmsg(account["emailaccount"], usageinfo)
            else:
                print "%s: %s" % (account["emailaccount"], usageinfo)
