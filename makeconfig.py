#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Edits the config file interactive and provides some basic
documentation about the config values.

If no previous config file exists the provided example will be used as
base if the user prefer.

MIT license applies, see the file COPYING.

TODO:
  - Add flag to edit an entire section. (-s name).
  - What happens if the ratio is entered with , instead of .?
  - Refactor when done =)

Martin Bagge <brother@bsnet.se>
Halmstad Studentkår, KAOS <kaos@karen.hh.se>

"""
import ConfigParser
from os.path import isfile, abspath, dirname, join, basename
import sys
from shutil import copyfile
import getopt

SCRIPTPATH = join(dirname(abspath(sys.argv[0])))
FILENAME = "config.ini"
CONFIGPATH = join(dirname(abspath(sys.argv[0])), FILENAME)
EXAMPLECONFIG = join(SCRIPTPATH, "config.ini.example")
ASKALL = False
TOUPDATE = ""


def helptext():
    print '''%s [-c /path/to/configfile] [[-a|-e settingname]|[-h]]

    -a, --all     Edit all settings.
    -e, --edit    Edit one specific setting.
    -c, --config  Path to config file. (Default: config.ini)
    -h, --help    This help text.

    If no option specified the current settings are shown.
    ''' % (basename(sys.argv[0]))

try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "ac:e:h",
                               ["all", "config", "edit", "help"]
                               )
except getopt.GetoptError as err:
    print str(err)
    helptext()
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        helptext()
        sys.exit()
    elif o in ("-a", "--all"):
        ASKALL = True
    elif o in ("-c", "--config"):
        CONFIGPATH = a
    elif o in ("-e", "--edit"):
        TOUPDATE = a
    else:
        assert False, "unhandled option"

if isfile(CONFIGPATH) is False and isfile(EXAMPLECONFIG) is True:
    try:
        copyfile(EXAMPLECONFIG, CONFIGPATH)
    except:
        print "Unable to use example file as base."
        sys.exit(1)

CONFIG = ConfigParser.RawConfigParser()
CONFIG.read(CONFIGPATH)

CFGSECTIONS = CONFIG.sections()


def editvalue(section, keyword, current, datatype="string"):
    """Checks if the option is up for editing and offers the user to
    change it.

    Arguments:
        section  (str): The name of the section in the ini file.
        keyword  (str): The name of the option to be edited.
        current  (str): The current value of the option.
        datatype (str): Can either be "string" (default) or "bool".
                        If the data type is bool the user is aked to
                        activate the value or not instead of asking
                        for text input.

    Returns:
        The value after editing, might be the current value actually.
    """
    if TOUPDATE == keyword or ASKALL is True:
        print "Updating %s in %s, current value: %s" % (
            keyword, section, current
        )
        try:
            if datatype == "string":
                print "Empty to use current value or 'skip' to omit."
                thevalue = raw_input("New value: ")
                if thevalue == "":
                    return current
            elif datatype == "bool":
                if raw_input("Set to True? (y/N) ").upper() == "Y":
                    thevalue = True
                else:
                    thevalue = False
            CONFIG.set(section, keyword, thevalue)
        except:
            sys.exit(2)
        return thevalue
    else:
        return current

if "API" in CFGSECTIONS:
    try:
        apiurl = CONFIG.get("API", "URL")
        if apiurl.endswith("/") is False:
            apiurl += "/"
    except ConfigParser.NoOptionError:
        apiurl = "https://api.glesys.com/email/"
    apiurl = editvalue("API", "URL", apiurl)

    try:
        apiuser = CONFIG.get("API", "user")
    except ConfigParser.NoOptionError:
        apiuser = "N/A"
    apiuser = editvalue("API", "user", apiuser)

    try:
        apikey = CONFIG.get("API", "key")
    except ConfigParser.NoOptionError:
        apikey = "the generated key"
    apikey = editvalue("API", "key", apikey)

    print """Current settings for API
    URL: %s
    user: %s
    key: %s
    """ % (apiurl, apiuser, apikey)
else:
    print "Section API missing in config file.\n"


if "Quota" in CFGSECTIONS:
    try:
        domainname = [
            x.strip() for x in CONFIG.get("Quota", "domainname").split(",")
        ]
    except ConfigParser.NoOptionError:
        domainname = "example.com, example.se"
    domainname = [
         x.strip() for x in editvalue(
             "Quota",
             "domainname",
             ", ".join(domainname)
         ).split(",")
    ]

    try:
        maxratio = CONFIG.getfloat("Quota", "ratio")
    except ValueError:
        # If the value in the config file can not be parsed as float
        # the default will be used.
        maxratio = 84.9
    except ConfigParser.NoOptionError:
        maxratio = 84.9
    # The ratio is a float and need . as separator.
    maxratio = editvalue("Quota", "ratio", maxratio)

    try:
        whitelist = [
            x.strip() for x in CONFIG.get("Quota", "whitelist").split(",")
        ]
    except ConfigParser.NoOptionError:
        whitelist = ""
    whitelist = [
        x.strip() for x in editvalue(
            "Quota",
            "whitelist",
            ",".join(whitelist)
        ).split(",")
    ]

    print """Current settings for Quota
    domainname: %s
    ratio: %s
    whitelist: %s
    """ % (", ".join(domainname), maxratio, ", ".join(whitelist))
else:
    print "Section Quota missing in config file.\n"


if "SMTP" in CFGSECTIONS:
    try:
        smtpenabled = CONFIG.getboolean("SMTP", "enabled")
    except ConfigParser.NoOptionError:
        smtpenabled = False
    except ValueError:
        # If the value can not be parsed as boolean the SMTP setting
        # will be disabled.
        smtpenabled = False
    smtpenabled = editvalue("SMTP", "enabled", smtpenabled, "bool")

    try:
        smtpserver = CONFIG.get("SMTP", "server")
    except ConfigParser.NoOptionError:
        smtpserver = "mail.glesys.com"
    smtpserver = editvalue("SMTP", "server", smtpserver)

    try:
        smtptls = CONFIG.getboolean("SMTP", "TLS")
    except ValueError:
        # If the value can not be parsed as boolean it will be treated
        # as True to not disable encryption by accident.
        smtptls = True
    except ConfigParser.NoOptionError:
        smtptls = True
    smtptls = editvalue("SMTP", "TLS", smtptls)

    try:
        smtpuser = CONFIG.get("SMTP", "user")
    except ConfigParser.NoOptionError:
        smtpuser = "u@example.com"
    smtpuser = editvalue("SMTP", "smtptls", smtptls)

    try:
        smtppassword = CONFIG.get("SMTP", "password")
    except ConfigParser.NoOptionError:
        smtppassword = "NotMyRealPassword!"
    smtppassword = editvalue("SMTP", "password", smtppassword)

    try:
        sender = CONFIG.get("SMTP", "sender")
    except ConfigParser.NoOptionError:
        sender = "someone@example.com"
    sender = editvalue("SMTP", "sender", sender)

    print """Current settings for SMTP:
    enabled: %s
    server: %s
    TLS: %s
    user: %s
    password: %s
    sender: %s
    """ % (smtpenabled, smtpserver, smtptls, smtpuser, smtppassword, sender)
else:
    print "Section SMTP missing in config file.\n"


if "Other" in CFGSECTIONS:
    try:
        debugmode = CONFIG.getboolean("Other", "debug")
    except ConfigParser.NoOptionError:
        debugmode = False
    debugmode = editvalue("Other", "debug", debugmode)

    try:
        talkative = CONFIG.getboolean("Other", "verbose")
    except ConfigParser.NoOptionError:
        talkative = False
    talkative = editvalue("Other", "verbos", talkative)

    print """Current settings for Other:
    verbose: %s
    debug: %s
    """ % (talkative, debugmode)
else:
    print "Section Other missing from config file.\n"

with open(CONFIGPATH, "wb") as configfile:
    CONFIG.write(configfile)
