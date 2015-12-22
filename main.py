import time
import os
import shutil
import threading
import requests
import re
import codecs
import subprocess
import services
import requests.packages.urllib3
import socket
import random

requests.packages.urllib3.disable_warnings()

version = 20151222.02
refresh_wait = [5, 30, 60, 300, 1800, 3600, 7200, 21600, 43200, 86400, 172800]
refresh = [[], [], [], [], [], [], [], [], [], [], []]
immediate_grab = []
total_count = 0
irc_server = 'irc.underworld.no'
irc_port = 6667
irc_channel_bot = '#newsgrabberbot'
irc_channel_main = '#newsgrabber'
irc_nick = 'newsbuddy'
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((irc_server, irc_port))
irc.send("USER " + irc_nick + " " + irc_nick + " " + irc_nick + " :This is the bot for " + irc_channel_main + ". https://github.com/ArchiveTeam/NewsGrabber.\n")
irc.send("NICK " + irc_nick + "\n")
irc.send("JOIN " + irc_channel_main + "\n")
irc.send("JOIN " + irc_channel_bot + "\n")

def irc_bot():
    while True:
        irc_message = irc.recv(2048)
        with open('irclog', 'a') as file:
            file.write(irc_message)
        if 'PING :' in irc_message:
            irc.send('PONG :\n')
        elif re.search(r'^:[^:]+:!help', irc_message):
            user = re.search(r'^:([^!]+)!', irc_message).group(1)
            irc_print(user, 'Hello! My options are:')
            irc_print(user, '\'!EMERGENCY_STOP\': This will stop the grab immediatly.')
            irc_print(user, '\'!im\', \'!immediate-grab\' or \'!immediate_grab\': This will make sure URLs are grabbed immediatly after they\'re found. Add \'remove\', \'rem\' or \'r\' to stop URLs from being grabbed immediatly after they\'re found.')
            irc_print(user, '\'!info\' or \'!information\': Request information about a service.')
        elif re.search(r'^:[^:]+:!info(?:formation)?', irc_message):
            user = re.search(r'^:([^!]+)!', irc_message).group(1)
            if not re.search(r'^:[^:]+:!info(?:formation)? web__[a-zA-Z0-9_]*', irc_message):
                irc_print(irc_channel_bot, user + ': What service do you want to have information about?')
            else:
                infoservice = re.search(r'^:[^:]+:!i(?:nfo(?:formation)?)? (web__[a-zA-Z0-9_]*)', irc_message).group(1)
                irc_print(irc_channel_bot, user + ': Service: ' + infoservice + '. Refreshtime: ' + str(refresh_wait[int(eval("services." + infoservice + ".refresh"))-1]) + ' seconds. URLs: ' + str(eval("services." + infoservice + ".urls")) + '. Regex: ' + str(eval("services." + infoservice + ".regex")) + '. Videoregex: ' + str(eval("services." + infoservice + ".videoregex")) + '. Liveregex: ' + str(eval("services." + infoservice + ".videoregex")) + '.')
                irc_print(irc_channel_bot, user + ': The script of this service is located here: https://github.com/ArchiveTeam/NewsGrabber/blob/master/services/' + infoservice + '.py')
        elif re.search(r'^:[^:]+:!EMERGENCY_STOP', irc_message):
            user = re.search(r'^:([^!]+)!', irc_message).group(1)
            irc_print(irc_channel_bot, user + ': Bot emergency stopped.')
            raise Exception('Bot emergency stopped.')
        elif re.search(r'^:[^:]+:!im(?:mediate[-_])?grab', irc_message):
            user = re.search(r'^:([^!]+)!', irc_message).group(1)
            if not re.search(r'^:[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?web__[a-zA-Z0-9_]*', irc_message):
                irc_print(irc_channel_bot, user + ': What service do you want to have grabbed immediatly?')
            else:
                imservice = re.search(r'^:[^:]+:!im(?:mediate[-_])?grab (?:r(?:em(?:ove)?)? )?(web__[a-zA-Z0-9_]*)', irc_message).group(1)
                if ' r' in irc_message:
                    immediate_grab.remove(imservice)
                    irc_print(irc_channel_bot, user + ': New URLs from service ' + imservice + ' will not be grabbed immediatly.')
                elif not imservice in immediate_grab:
                    immediate_grab.append(imservice)
                    irc_print(irc_channel_bot, user + ': New URLs from service ' + imservice + ' will be grabbed immediatly.')
def irc_bot_count():
    global total_count
    sleep_time = 900
    while True:
        irc_print(irc_channel_bot, str(total_count) + ' URLs added in the last ' + str(int(sleep_time/60)) + ' minutes.')
        total_count = 0
        time.sleep(sleep_time)

def irc_print(channel, message):
    irc.send("PRIVMSG "+ channel +" :" + message + "\n")
    print("IRC BOT: " + message)

def checkrefresh():
    while True:
        new_services = 0
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
                        for refreshlist in refresh:
                            while service[:-3] in refreshlist:
                                refreshlist.remove(service[:-3])
                        refresh[int(eval("services." + service[:-3] + ".refresh"))-1].append(service[:-3])
                        new_services += 1
                        print('Found service ' + service[:-3] + '.')
        if new_services == 1:
            irc_print(irc_channel_bot, 'Found and updated ' + str(new_services) + ' service.')
        elif new_services != 0:
            irc_print(irc_channel_bot, 'Found and updated ' + str(new_services) + ' services.')
        time.sleep(300)

def checkurl(service, urlnum, url, regexes, videoregexes, liveregexes):
    global total_count
    imgrabfiles = []
    tries = 0
    while tries < 5:
        try:
            response = requests.get(url)
        except Exception as exception:
            tries += 1
            with open('exceptions', 'a') as exceptions:
                if tries == 5:
                    exceptions.write(str(version) + ' ' + str(tries) + ' ' + url + '\n' + str(exception) + '\n\n')
                #    irc_print(irc_channel_bot, str(version) + ' ' + str(tries) + ' ' + url + ' EXCEPTION ' + str(exception))
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
            url = re.search(r'([^#]+)', url).group(1)
            for extractedurl in re.findall(r"'(index\.php[^']+)'", response.text):
                extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
                oldextractedurls.append(re.match(r'^(https?://.+/)', url).group(1) + extractedurl)
            for extractedurl in re.findall('(....=(?P<quote>[\'"]).*?(?P=quote))', response.text):
                extractedstart = re.search(r'^(....)', extractedurl[0]).group(1)
                extractedurl = re.search('^....=[\'"](.*?)[\'"]$', extractedurl[0]).group(1)
                extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
                if extractedurl.startswith('//'):
                    oldextractedurls.append("http:" + extractedurl)
                elif extractedurl.startswith('/'):
                    oldextractedurls.append(re.search(r'^(https?:\/\/[^\/]+)', url).group(1) + extractedurl)
                elif extractedurl.startswith('https://') or extractedurl.startswith('http://'):
                    oldextractedurls.append(extractedurl)
                elif extractedurl.startswith('?'):
                    oldextractedurls.append(re.search(r'^(https?:\/\/[^\?]+)', url).group(1) + extractedurl)
                elif extractedurl.startswith('./'):
                    if re.search(r'^https?:\/\/.+\/', url):
                        oldextractedurls.append(re.search(r'^(https?:\/\/.+)\/', url).group(1) + '/' + re.search(r'^\.\/(.+)', extractedurl).group(1))
                    else:
                        oldextractedurls.append(re.search(r'^(https?:\/\/.+)', url).group(1) + '/' + re.search(r'^\.\/(.+)', extractedurl).group(1))
                elif extractedurl.startswith('../'):
                    tempurl = url
                    tempextractedurl = extractedurl
                    while tempextractedurl.startswith('../'):
                        if not re.search(r'^https?://[^\/]+\/$', tempurl):
                            tempurl = re.search(r'^(.+\/)[^\/]*\/', tempurl).group(1)
                        tempextractedurl = re.search(r'^\.\.\/(.*)', tempextractedurl).group(1)
                    oldextractedurls.append(tempurl + tempextractedurl)
                elif extractedstart == 'href':
                    if re.search(r'^https?:\/\/.+\/', url):
                        oldextractedurls.append(re.search(r'^(https?:\/\/.+)\/', url).group(1) + '/' + extractedurl)
                    else:
                        oldextractedurls.append(re.search(r'^(https?:\/\/.+)', url).group(1) + '/' + extractedurl)
            for extractedurl in re.findall(r'>[^<a-zA-Z0-9]*(https?://[^<]+)<', response.text):
                extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
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
            imgrabfiles.append(str(random.random()))
            imgrabfiles.append(str(random.random()))
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
                        if extractedurl in extractedvideourls and service in immediate_grab:
                            filename = 'list-videos-immediate' + imgrabfiles[0]
                            with codecs.open(filename, 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        elif service in immediate_grab:
                            filename = 'list-immediate' + imgrabfiles[1]
                            with codecs.open(filename, 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        if extractedurl in extractedvideourls:
                            with codecs.open('list-videos', 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        else:
                            with codecs.open('list', 'a', 'utf-8') as listurls:
                                if not extractedurl in listfile:
                                    listurls.write(extractedurl + '\n')
                        count += 1
            if os.path.isfile('list-videos-immediate' + imgrabfiles[0]):
                listname = 'list-videos-immediate' + imgrabfiles[0]
                irc_print(irc_channel_bot, 'Started immediate videos grab for service ' + service + '.')
                threading.Thread(target = grablist, args = (listname,)).start()
            elif os.path.isfile('list-immediate' + imgrabfiles[1]):
                listname = 'list-immediate' + imgrabfiles[1]
                irc_print(irc_channel_bot, 'Started immediate normal grab for service ' + service + '.')
                threading.Thread(target = grablist, args = (listname,)).start()
            print('Extracted ' + str(count) + ' URLs from service ' + service + ' for URL ' + url + '.')
            total_count += count

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
            threading.Thread(target=grablist, args=('list_temp',)).start()
            irc_print(irc_channel_bot, "Started normal grab.")
        time.sleep(10)
        if os.path.isfile('list-videos'):
            os.rename('list-videos', 'list-videos_temp')
            threading.Thread(target=grablist, args=('list-videos_temp',)).start()
            irc_print(irc_channel_bot, "Started videos grab.")
        time.sleep(3580)

def grablist(listname):
    videostring = ''
    if '-videos' in listname:
        videostring = ' --wpull-args=--no-check-certificate --wpull-args=--youtube-dl'
    os.system('~/.local/bin/grab-site --input-file ' + listname + ' --level=0 --no-sitemaps --concurrency=5 --1 --warc-max-size=524288000' + videostring + ' --wpull-args=--timeout=300 > /dev/null 2>&1')

def main():
    pause_length = 10
    threading.Thread(target = irc_bot).start()
    time.sleep(pause_length*2)
    irc_print(irc_channel_bot, 'Hello!')
    irc_print(irc_channel_bot, 'Version ' + str(version) + '.')
    irc_print(irc_channel_main, 'Hello! I\'ve just been (re)started. Follow my newsgrabs in #newsgrabberbot')
    irc_print(irc_channel_bot, 'Script started.')
    threading.Thread(target = irc_bot_count).start()
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
        threading.Thread(target = refresh_grab, args = (i,)).start()
    threading.Thread(target = grab).start()

if __name__ == '__main__':
    main()