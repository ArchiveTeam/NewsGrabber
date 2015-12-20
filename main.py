import time
import os
import shutil
import threading
import requests
import re
import codecs
import subprocess
import services

version = 20151218.01
refresh_wait = [5, 30, 60, 300, 1800, 3600, 7200, 21600, 43200, 86400, 172800]
refresh = [[], [], [], [], [], [], [], [], [], [], []]

def checkrefresh():
    while True:
        if os.path.isdir('./services'):
            shutil.rmtree('./services')
        os.system('git clone https://github.com/ArchiveTeam/NewsGrabber.git')
        shutil.copytree('./NewsGrabber/services', './services')
        shutil.rmtree('./NewsGrabber')
        reload(services)
        for root, dirs, files in os.walk("./services"):
            for service in files:
                if service.startswith("web__") and service.endswith(".py"):
                    if not service[:-3] in refresh[int(eval("services." + service[:-3] + ".refresh"))-1]:
                        refresh[int(eval("services." + service[:-3] + ".refresh"))-1].append(service[:-3])
                        print('Found service ' + service[:-3])
        time.sleep(300)

def checkurl(service, urlnum, url, regexes, videoregexes, liveregexes):
    tries = 0
    while tries < 5:
        try:
            response = requests.get(url)
        except Exception as exception:
            tries += 1
            with open('exceptions', 'a') as exceptions:
                exceptions.write(str(version) + ' ' + str(tries) + ' ' + url + '\n' + str(exception) + '\n\n')
        try:
            response
        except NameError:
            pass
        else:
            tries = 5
            oldextractedurls = []
            extractedurls = []
            extractedvideourls = []
            count = 0
            for extractedurl in re.findall(r"'(index\.php[^']+)'", response.text):
                oldextractedurls.append(re.match(r'^(https?://.+/)', url).group(1) + extractedurl)
            for extractedurl in re.findall(r'="(https?://[^"]+)"', response.text):
                oldextractedurls.append(extractedurl)
            for extractedurl in re.findall(r"='(https?://[^']+)'", response.text):
                oldextractedurls.append(extractedurl)
            for extractedurl in re.findall(r'="(/[^"]+)"', response.text):
                if extractedurl.startswith('//'):
                    oldextractedurls.append("http:" + extractedurl)
                else:
                    oldextractedurls.append(re.match(r'^(https?://[^/]+)', url).group(1) + extractedurl)
            for extractedurl in re.findall(r"='(/[^']+)'", response.text):
                if extractedurl.startswith('//'):
                    oldextractedurls.append("http:" + extractedurl)
                else:
                    oldextractedurls.append(re.match(r'^(https?://[^/]+)', url).group(1) + extractedurl)
            for extractedurl in re.findall(r'>[^<a-zA-Z0-9]*(https?://[^<]+)<', response.text):
                oldextractedurls.append(extractedurl)
            for extractedurl in oldextractedurls:
                if '?' in extractedurl:
                    oldextractedurls.append(extractedurl.split('?')[0])
                for extractedurl in oldextractedurls:
                for regex in regexes:
                    if re.search(regex, extractedurl) and not extractedurl in extractedurls:
                        extractedurls.append(extractedurl)
                        break
                for extractedurl in extractedurls:
                for regex in videoregexes:
                    if re.search(regex, extractedurl) and not extractedurl in extractedvideourls:
                        extractedvideourls.append(extractedurl)
                        break
            if not os.path.isdir("./donefiles"):
                os.makedirs("./donefiles")
            if os.path.isfile('./donefiles/' + service):
                donefile = codecs.open('./donefiles/' + service, 'r', 'utf-8').read()
            else:
                donefile = 'NOTHING'
            if os.path.isfile('list'):
                listfile = codecs.open('list', 'r', 'utf-8').read()
            else:
                listfile = 'NOTHING'
            with codecs.open('./donefiles/' + service + urlnum + '_webpage', 'w', 'utf-8') as pagefile:
                pagefile.write(response.text)
            for extractedurl in extractedurls:
                extractedurl = re.sub("&amp;", "&", extractedurl)
                with codecs.open('./donefiles/' + service, 'a', 'utf-8') as doneurls:
                    if not extractedurl in donefile:
                        #print(extractedurl)
                        for regex in liveregexes:
                            if re.search(regex, extractedurl):
                                break
                        else:
                            doneurls.write(extractedurl + '\n')
                        if extractedurl in extractedvideourls:
                            with codecs.open('list-videos', 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        else:
                            with codecs.open('list', 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        count += 1
            print('Extracted ' + str(count) + ' URLs from service ' + service)

def refresh_grab(i):
    while True:
        for service in refresh[i]:
            urlnum = 0
            for url in eval("services." + service + ".urls"):
                threading.Thread(target = checkurl, args = (service, str(urlnum), url, eval("services." + service + ".regex"), eval("services." + service + ".videoregex"), eval("services." + service + ".liveregex"))).start()
                urlnum += 1
        time.sleep(refresh_wait[i])

def dashboard():
    os.system('~/.local/bin/gs-server')

def processfiles():
    while True:
        os.system('python movefiles.py')
        command2 = subprocess.Popen(['python', 'uploader.py'])
        time.sleep(300)

def grab():
    while True:
        time.sleep(10)
        if os.path.isfile('list_temp'):
            os.remove('list_temp')
        if os.path.isfile('list-videos_temp'):
            os.remove('list-videos_temp')
        if os.path.isfile('list'):
            os.rename('list', 'list_temp')
            threading.Thread(target=grablist).start()
            print("Started normal grab")
        if os.path.isfile('list-videos'):
            os.rename('list-videos', 'list-videos_temp')
            threading.Thread(target=grablistvideos).start()
            print("Started videos grab")

        time.sleep(3590)

def grablist():
    os.system('~/.local/bin/grab-site --input-file list_temp --level=0 --no-sitemaps --concurrency=5 --1 --warc-max-size=524288000 > /dev/null 2>&1')

def grablistvideos():
    os.system('~/.local/bin/grab-site --input-file list-videos_temp --level=0 --no-sitemaps --concurrency=5 --1 --warc-max-size=524288000 --wpull-args=--no-check-certificate --wpull-args=--youtube-dl > /dev/null 2>&1')

def main():
    pause_length = 10
    if not os.path.isdir("./ready"):
        os.makedirs("./ready")
    for root, dirs, files in os.walk("./ready"):
        for file in files:
            if file.endswith(".upload"):
                os.remove(os.path.join(root, file))
    threading.Thread(target = checkrefresh).start()
    time.sleep(pause_length)
    threading.Thread(target = dashboard).start()
    threading.Thread(target = processfiles).start()
    for i in range(len(refresh)):
        print(i)
        threading.Thread(target = refresh_grab, args = (i,)).start()
    threading.Thread(target = grab).start()

if __name__ == '__main__':
    main()
