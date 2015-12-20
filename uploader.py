import os
import re
import subprocess
import time
import sys

for root, dirs, files in os.walk("./ready"):
    for file in files:
        date = re.search(r'([0-9][0-9][0-9][0-9]\-[0-9][0-9]\-[0-9][0-9])', file).group(1)
        date2 = re.sub('-', '', date)
        if re.match(r'news', file) and file.endswith(".warc.gz"):
            if not os.path.isfile(os.path.join(root, file) + ".upload"):
                open(os.path.join(root, file) + ".upload", 'a').close()
                command = subprocess.Popen(['python', 'upload.py', file, date])
                time.sleep(1)
sys.exit()
