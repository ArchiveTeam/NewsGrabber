import os
import time
import requests
import re
import sys

name = sys.argv[1]
date1 = sys.argv[2]
date = re.sub('-', '', date1)

os.system('ia upload newssites-{0} ./ready/{1} --metadata="title:newssites-{0}" --metadata="mediatype:web" --metadata="collection:opensource" --metadata="date:{2}" --checksum --size-hint=214748364800 --delete > /dev/null 2>&1'.format(date, name, date1))
os.remove("./ready/" + name + ".upload")
if os.path.isfile('./ready/' + name):
    print(name + ' upload unsuccessful')
else:
    print(name + ' uploaded to newssites-' + date)