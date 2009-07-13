#!/bin/bash
PYTHON=/usr/bin/python
NOTIFY=/path/to/your/notify-roundup.py
CONFIG=/path/to/your/notify-roundup.ini
REPOS=`/bin/pwd`
CMD="/usr/bin/hg log `/bin/pwd` --rev=tip"
REV=`$CMD | grep changeset`
PYTHONPATH=/path/to/your/roundup/instance "$PYTHON" "$NOTIFY" "$CONFIG" "$REPOS" "$REV"
