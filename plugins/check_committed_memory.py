#!/usr/bin/python3
# Overcommitting memory is bad! Keep an eye on it.
# Author: Xiwen Cheng <xiwen.cheng@mendix.com>

import re
from optparse import OptionParser

default_opts = {'warning': 90, 'critical': 100}
source = "/proc/meminfo"
regex_line = (re.compile(r'^(?P<key>\S+):\s+(?P<value>\S+)'))

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# parse arguments
parser = OptionParser()
parser.add_option("-w", "--warning", dest="warning", help="Warning threshold committed percentage")
parser.add_option("-c", "--critical", dest="critical",
                  help="Critical threshold committed percentage")
(options, args) = parser.parse_args()


# set defaults
if not options.warning:
    options.warning = default_opts['warning']

if not options.critical:
    options.critical = default_opts['critical']

# convert to int, needed for comparison
options.warning = int(options.warning)
options.critical = int(options.critical)

try:
    infile = open(source, "r")
except IOError as e:
    print("Error - %s" % e)
    exit(STATE_UNKNOWN)

lines = infile.readlines()
infile.close()

# default values
total = 0
committed = 0

for line in lines:
    match = regex_line.match(line)
    if match:
        if match.groupdict()['key'] == "MemTotal":
            total = int(match.groupdict()['value'])
        elif match.groupdict()['key'] == "Committed_AS":
            committed = int(match.groupdict()['value'])
percent = int(float(committed) / total * 100)

if percent >= options.critical:
    state = STATE_CRITICAL
    state_label = "CRITICAL"
elif percent >= options.warning:
    state = STATE_WARNING
    state_label = "WARNING"
else:
    state = STATE_OK
    state_label = "OK"

print("%s - Memory committed: %d kB of %d kB (%d%%)" % (state_label, committed, total, percent))
print("Thresholds: warn = %d%%, crit = %d%%" % (options.warning, options.critical))
exit(state)

# vim:sw=4:ts=4:expandtab
