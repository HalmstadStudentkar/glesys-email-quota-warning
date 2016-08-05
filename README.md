# GleSYS E-mail quota warning

Extract all users and check if they are over a certain ratio for mail
quota usage. Send a message to them hilighting the fact.

# GleSYS API

You need to visit the GleSYS customer panel and activate the API and
add a user+key combination that can access the email settings on your
behalf.

# Dependencies

Uses the httplib2 python module for communication. Everything else
should be available in standard distribution.

The email warning is sent using SMTP communication, either use the
GleSYS mailserver or you need your own. Default setting is to print
the information to STDOUT only, in that case there are no SMTP
dependency.

# Configuration

Copy the mailquotaconfig.ini.example file to
mailquotaconfig.ini.example. Edit the file for your settings.

## In the future....

If you are not very comfortable with editing configuration files use
the wizard also included in the repository. Also usable for editing a
already present file.

Start wizard: `./makeconfig.py`

...but that's for the future. See [mb-configmaker](https://github.com/HalmstadStudentkar/glesys-email-quota-warning/tree/mb-configmaker) branch.

# How to execute

Bare minimum configuration is User and Key to the API and the domain
name to execute the check.

If you need to get a complete list of the current usage state change
the verbose config to True otherwise only information for accounts
over the ratio will be shown and could render that no output is shown
(when no account are over the ratio).

`./warning.py`

## Automation

Use cron to make it execute every Monday at 6 in the morning.
0 6 * * 1 /path/to/glesys-email-quota-warning/warning.py

# Credits and license

The code is written by Martin Bagge / brother <brother@bsnet.se> on
behalf of Halmstad Studentkår, KAOS. The code is licensed MIT, patches
and suggestions are welcome.

Contact KAOS at kaos@karen.hh.se if needed.
