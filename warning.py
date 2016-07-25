#!/usr/bin/python
# -*- coding: utf-8 -*-
# MIT license applies, see the file COPYING.
# Martin Bagge <brother@bsnet.se>
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


# TODO: Need to write proper docs.
def apirequest(target, data):
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


# TODO: Need to write proper docs.
def fetchAccounts(domain):
    return apirequest("list", {'domainname': domain})


# TODO: Need to write proper docs.
def fetchQuota(address):
    return apirequest("quota", {'emailaccount': address})["response"]["quota"]


# TODO: Need to write proper docs.
def sendmsg(recipient, information):
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

    accountlist = fetchAccounts(name)
    for account in accountlist["response"]["list"]["emailaccounts"]:
        quotaobj = fetchQuota(account["emailaccount"])
        used = float(quotaobj["used"]["amount"])
        allowed = float(quotaobj["total"]["max"])
        ratio = round((used / allowed) * 100, 2)
        if ratio > maxratio:
            usageinfo = str(used)+" av "+str(allowed)+" ("+str(ratio)+"%)"
            if smtpenabled:
                sendmsg(account["emailaccount"], usageinfo)
            else:
                print "%s: %s" % (account["emailaccount"], usageinfo)
