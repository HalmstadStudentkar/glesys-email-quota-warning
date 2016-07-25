# GleSYS E-mail quota warning

Extract all users and check if they are over a certain ratio for mail
quota usage. Send a message to them hilighting the fact.

# GleSYS API

You need to visit the GleSYS customer panel and activate the API and
add a user+key combination that can access the email settings on your
behalf.

# Configuration

Copy the mailquotaconfig.ini.example file to
mailquotaconfig.ini.example.  Edit the file for your settings.

If you are not very comfortable with editing configuration files use
the wizard also included in the repository. Also usable for editing a
already present file.

Start wizard:
 ./makeconfig.py

# Credits and license

The codet is written by Martin Bagge / brother <brother@bsnet.se> on
behalf of Halmstad Studentkår, KAOS. The code is licensed MIT, patches
and suggestions are welcome.

Contact KAOS at kaos@karen.hh.se if needed.
