#!/usr/bin/env python
#
# Plugin to check for Certificates that will be expiring soon, or has expired (BAD!)
# It reads the configuration file at '/etc/certs.cfg' (standard). Each line is the
# full path to a certificate to be monitored. Empty lines and those with # (hash
# sign) as prefix are skipped. Useful for comments.
#
# Author: Xiwen Cheng <xiwen.cheng@mendix.com>

import os
import re
import sys
from datetime import datetime, timedelta
import getopt
from optparse import OptionParser
from OpenSSL import crypto, SSL
import operator

default_opts = {'warning': 30, 'critical': 10, 'config': '/etc/ssl/check_certs.cfg'}
MARKER_BEGIN = "-----BEGIN CERTIFICATE-----"
MARKER_END = "-----END CERTIFICATE-----"

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# parse arguments
parser = OptionParser()
parser.add_option("-w", "--warning",
                  dest="warning",
                  help="Warning threshold expiration in days")
parser.add_option("-c", "--critical",
                  dest="critical",
                  help="Critical threshold expiration in days")
parser.add_option("-f", "--file",
                  dest="filename",
                  help="File containing list of certificates to check")
(options, args) = parser.parse_args()


# set defaults
if not options.warning:
    options.warning = default_opts['warning']

if not options.critical:
    options.critical = default_opts['critical']

if not options.filename:
    options.filename = default_opts['config']

# convert to int, needed for comparison
options.warning = int(options.warning)
options.critical = int(options.critical)

fileExists = os.path.exists(options.filename)

if(fileExists is False):
    print "Error: File %s doesn't exist!" % options.filename
    exit(STATE_UNKNOWN)

try:
    infile = open(options.filename, "r")
except IOError, e:
    print "Error - %s" % e
    exit(STATE_UNKNOWN)

config_lines = infile.readlines()
infile.close()

today = datetime.now()
warning_count = 0
critical_count = 0
files_count = 0
ok_count = 0
summary = list()
files = []


def expand_file_list(path):
    my_files = []
    if os.path.isfile(path):
        my_files.append(path)
    elif os.path.isdir(path):
        my_files = [os.path.join(path, i) for i in os.listdir(path)]
    return my_files

for config_line in config_lines:
    name = config_line.strip()
    # support for comments in config file, must have prefix #
    if name.startswith('#') or len(name) <= 0:
        continue
    paths = expand_file_list(name)
    files = files + paths


for fname in files:
    # skip al non crt and pem files
    if fname.endswith(".crt") or fname.endswith(".pem"):
        pass
    else:
        continue

    files_count = files_count + 1
    try:
        buffer = open(fname, 'r').read()
    except IOError, e:
        critical_count = critical_count + 1
        summary.append({'days': -1, 'status': "[CRIT]", 'fname': fname, 'cn': 'MISSING'})
        continue

    certs = buffer.split(MARKER_END)
    for cert in certs:
        # filter out empty lines
        if len(cert.strip()) == 0:
            continue
        mybuf = cert + MARKER_END

        mykey = crypto.load_certificate(crypto.FILETYPE_PEM, mybuf)
        cn = mykey.get_subject().commonName
        notafter = datetime.strptime(mykey.get_notAfter(), "%Y%m%d%H%M%SZ")
        diff = notafter - today
        days = diff.days
        if days <= options.critical:
            critical_count = critical_count + 1
            summary.append({'days': days, 'status': "[CRIT]", 'fname': fname, 'cn': cn})
        elif days <= options.warning:
            warning_count = warning_count + 1
            summary.append({'days': days, 'status': "[WARN]", 'fname': fname, 'cn': cn})
        else:
            ok_count = ok_count + 1
            summary.append({'days': days, 'status': "", 'fname': fname, 'cn': cn})

# stats
total_count = ok_count + warning_count + critical_count
if critical_count > 0:
    state = STATE_CRITICAL
    state_label = "CRITICAL"
elif warning_count > 0:
    state = STATE_WARNING
    state_label = "WARNING"
else:
    state = STATE_OK
    state_label = "OK"


print("%s - Certificates: ok = %d, warn = %d, crit = %d (%d certs in %d files)" %
      (state_label, ok_count, warning_count, critical_count, total_count, files_count))
print("Thresholds: warn = %d days, crit = %d days" % (options.warning, options.critical))

# sort
summary.sort(key=operator.itemgetter('days'))
for info in summary:
    print("%s (%s) expires in %d days %s" %
          (info['cn'], info['fname'], info['days'], info['status']))

exit(state)
