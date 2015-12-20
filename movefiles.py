import os
import shutil
import re

list = []
done = True

def check(files, num):
    for file in files:
        if file.endswith("0000" + num + ".warc.gz"):
            return True
    return False

def warcnum(files):
    count = 0
    for root, dirs, files in os.walk("./" + folder):
        for file in files:
            #print(file)
            if file.endswith(".warc.gz"):
                count += 1
        return count

for folder in next(os.walk('.'))[1]:
    if not (folder == 'services' or folder == 'temp' or folder == 'donefiles'):
        for root, dirs, files in os.walk("./" + folder):
            if (check(files, "0") == False or check(files, "1") == True) and not folder == "ready":
                startnum = "0"
                firstnum = None
                moved = False
                while True:
                    if not os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
                        if firstnum > 0:
                            break
                    if os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
                        if firstnum == None:
                            firstnum = int(startnum)
                        if not startnum == "0" and not firstnum == int(startnum):
                            #print(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"))
                            moved = True
                            os.rename(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"), "./ready/" + folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz")
                    startnum = str(int(startnum) + 1)
                    if warcnum(folder) == 1:
                        break
                    if warcnum(folder) == 2 and os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz"):
                        break
        if os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz") and not folder == "ready":
            for root, dirs, files in os.walk("./" + folder):
                for file in files:
                    if file.endswith(".warc.gz"):
                        list.append("./ready/" + file)
                        os.rename(os.path.join(root, file), "./ready/" + file)
                for file in files:
                    if file.endswith(".warc.gz") and not os.path.isfile("./ready/" + file):
                        #print("./ready/" + file)
                        done = False
                if done == True:
                    shutil.rmtree("./" + folder)
for root, dirs, files in os.walk("./ready"):
    for file in files:
        os.rename(os.path.join(root, file), os.path.join(root, re.sub(".*-list(?:-videos)?_temp", "news", file)))
print("All finished WARCs have been moved")
