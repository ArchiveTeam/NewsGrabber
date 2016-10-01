import threading
import os
import shutil
import sys
import time
import re
import urllib

import requests

if os.path.isdir('services'):
    shutil.rmtree('services')
if not os.path.isdir('services'):
    os.makedirs('services')
if not os.path.isfile('services/__init__.py'):
    open('services/__init__.py', 'w').close()

import file
import services
import settings

reload(sys)
sys.setdefaultencoding("utf-8")


class RunServices(threading.Thread):

    """Services are here started and stopped."""

    def __init__(self):
        threading.Thread.__init__(self)
        self.services = []
        self.assigned_services = []

    def run(self):
        self.refresh()

    def refresh(self):
        while True:
            for file_ in [file_ for file_ in os.listdir(
                  settings.dir_assigned_services) if os.path.isfile(
                  os.path.join(settings.dir_assigned_services, file_))]:
                while not settings.run_services_running:
                    time.sleep(1)
                read_file = file.File(os.path.join(
                    settings.dir_assigned_services, file_))
                services_new = read_file.read_json()
                self.assigned_services = services_new['services']
                if services_new['nick'] != settings.irc_nick:
                    settings.irc_bot.set_nick(services_new['nick'])
                print(self.assigned_services)
                settings.irc_bot.send('PRIVMSG', '{i} services assigned.'.format(
                    i=len(self.assigned_services)),
                    settings.irc_channel_bot)
                os.remove(os.path.join(settings.dir_assigned_services, file_))
                self.refresh_services()
            time.sleep(1)

    def refresh_services(self):
        if os.path.isdir('services'):
            shutil.rmtree('services')
        os.system('git clone https://github.com/ArchiveTeam/NewsGrabber.git')
        shutil.copytree(os.path.join('NewsGrabber', 'services'), 'services')
        shutil.rmtree('NewsGrabber')
        reload(services)
        self.start_services()

    def start_services(self):
        for key, value in settings.services.iteritems():
            settings.services[key].running = False
        for file in [file for file in os.listdir('services') if file.startswith(
              'web__') and file.endswith('.py')]:
            service_name = file.replace('.py', '')
            if not service_name in self.assigned_services:
                continue
            self.services.append(service_name)
            settings.services[service_name] = Service(service_name)
            settings.services[service_name].daemon = True
            settings.services[service_name].start()

    def clear(self):
        for key, value in settings.services.iteritems():
            del value.extracted_urls[:]


class Upload(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.urls = []
        self.target = file.File(settings.target)
        self.url_files = {}

    def run(self):
        self.upload_url_lists()

    def add_url(self, url, service, service_version, service_url, sort, live, imgrab):
        self.urls.append({'url': url,
            'service': service,
            'script_version': settings.version,
            'service_version': service_version,
            'service_url': service_url,
            'sort': sort,
            'live': live,
            'time': int(time.time()),
            'immediate_grab': imgrab,
            'bot_nick': settings.irc_nick})

    def upload_url_lists(self):
        while True:
            while not settings.upload_running:
                time.sleep(1)
            urls = list(self.urls)
            self.urls = list(self.urls[len(urls):])
            if len(urls) != 0:
                target = self.target.read()
                file_name = settings.irc_nick + '_' + str(time.time())
                self.url_files[file_name] = file.File(file_name)
                self.url_files[file_name].write_json(urls)
                os.system('rsync -avz --no-o --no-g --progress --remove-source-files {file_name} {target}'.format(
                    **locals()))
                if os.path.isfile(file_name):
                    settings.irc_bot.send('PRIVMSG', '{file_name} synced unsuccessful to main server.'.format(
                        **locals()), settings.irc_channel_bot)
                    self.urls += self.url_files[file_name].read_json()
                    os.remove(file_name)
            time.sleep(60)


class Service(threading.Thread):

    """This class is used to manage and run a service."""

    global_refresh = None

    def __init__(self, service_name):
        threading.Thread.__init__(self)
        self.service_name = service_name
        self.service_refresh = None
        self.service_urls = None
        self.service_regex = None
        self.service_regex_video = None
        self.service_regex_live = None
        self.service_version = None
        self.service_wikidata = None
        self.service_immediate = False
        self.service_urls = []
        self.extracted_urls = []
        self.immediate_grab = False
        self.running = True

    def run(self):
        print(self.service_name)
        self.get_data()
        self.process_urls()

    def get_data(self):
        self.service_refresh = eval('services.{service_name}.refresh'.format(
            service_name=self.service_name))
        self.service_urls = eval('services.{service_name}.urls'.format(
            service_name=self.service_name))
        self.service_regex = eval('services.{service_name}.regex'.format(
            service_name=self.service_name))
        try:
            self.service_regex_video = eval('services.{service_name}.videoregex'.format(
                service_name=self.service_name)) + settings.standard_regex_video
        except:
            self.service_regex_video = settings.standard_regex_video
        try:
            self.service_regex_live = eval('services.{service_name}.liveregex'.format(
                service_name=self.service_name)) + settings.standard_regex_live
        except:
            self.service_regex_live = settings.standard_regex_live
        self.service_version = eval('services.{service_name}.version'.format(
            service_name=self.service_name))
        try:
            self.service_wikidata = eval('services.{service_name}.wikidata'.format(
                service_name=self.service_name))
        except:
            self.service_wikidata = None

    def process_urls(self):
        while self.running:
            for service_url in self.service_urls:
                while not settings.run_services_running:
                    time.sleep(1)
                for url in self.extract_urls(service_url, self.service_regex):
                    if url in self.extracted_urls:
                        continue
                    for regex in self.service_regex_live:
                        if re.search(regex, url, re.I):
                            url_live = True
                            break
                    else:
                        url_live = False
                    for regex in self.service_regex_video:
                        if re.search(regex, url, re.I):
                            settings.upload.add_url(url,
                                self.service_name, self.service_version,
                                service_url, 'video', url_live,
                                self.immediate_grab)
                            break
                    else:
                        settings.upload.add_url(url, self.service_name,
                           self.service_version, service_url, 'normal',
                           url_live, self.immediate_grab)
                    if not url_live:
                        self.extracted_urls.append(url)
            if Service.global_refresh and \
                  Service.global_refresh < self.service_refresh:
                refresh = Service.global_refresh
            else:
                refresh = self.service_refresh
            time.sleep(refresh)

    @classmethod
    def set_global_refresh(cls, refresh):
        cls.global_refresh = refresh

    @classmethod
    def get_global_refresh(cls):
        return cls.global_refresh

    @staticmethod
    def extract_urls(url, regexes):
        extractedurls = []
        tries = 0
        while tries < 10:
            while not settings.run_services_running:
                time.sleep(1)
            try:
                response = requests.get(url, headers={'User-Agent': 'ArchiveTeam; Googlebot/2.1'})
                response.encoding = 'utf-8'
            except Exception as exception:
                tries += 1
            try:
                response
            except NameError:
                pass
            else:
                tries = 10
                oldextractedurls = []
                extractedvideourls = []
                url = re.search(r'([^#]+)', url).group(1)
                for extractedurl in re.findall(r"'(index\.php[^']+)'", response.text, re.I):
                    extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
                    oldextractedurls.append(re.match(r'^(https?://.+/)', url, re.I).group(1) + extractedurl)
                for extractedurl in re.findall('(....=(?P<quote>[\'"]).*?(?P=quote))', response.text):
                    extractedstart = re.search(r'^(....)', extractedurl[0]).group(1)
                    extractedurl = re.search('^....=[\'"](.*?)[\'"]$', extractedurl[0]).group(1)
                    extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
                    extractedurl = extractedurl.replace('%3A', ':').replace('%2F', '/')
                    if extractedurl.startswith('http:\/\/') or extractedurl.startswith('https:\/\/') or extractedurl.startswith('HTTP:\/\/') or extractedurl.startswith('HTTPS:\/\/'):
                        extractedurl = extractedurl.replace('\/', '/')
                    elif extractedurl.startswith('//'):
                        oldextractedurls.append("http:" + extractedurl)
                    elif extractedurl.startswith('/'):
                        oldextractedurls.append(re.search(r'^(https?:\/\/[^\/]+)', url, re.I).group(1) + extractedurl)
                    elif re.search(r'^https?:?\/\/?', extractedurl, re.I):
                        oldextractedurls.append(extractedurl.replace(re.search(r'^(https?:?\/\/?)', extractedurl, re.I).group(1), re.search(r'^(https?)', extractedurl, re.I).group(1) + '://'))
                    elif extractedurl.startswith('?'):
                        oldextractedurls.append(re.search(r'^(https?:\/\/[^\?]+)', url, re.I).group(1) + extractedurl)
                    elif extractedurl.startswith('./'):
                        if re.search(r'^https?:\/\/.*\/', url, re.I):
                            oldextractedurls.append(re.search(r'^(https?:\/\/.*)\/', url, re.I).group(1) + '/' + re.search(r'^\.\/(.*)', extractedurl).group(1))
                        else:
                            oldextractedurls.append(re.search(r'^(https?:\/\/.*)', url, re.I).group(1) + '/' + re.search(r'^\.\/(.*)', extractedurl).group(1))
                    elif extractedurl.startswith('../'):
                        tempurl = url
                        tempextractedurl = extractedurl
                        while tempextractedurl.startswith('../'):
                            if not re.search(r'^https?://[^\/]+\/$', tempurl, re.I):
                                tempurl = re.search(r'^(.*\/)[^\/]*\/', tempurl).group(1)
                            tempextractedurl = re.search(r'^\.\.\/(.*)', tempextractedurl).group(1)
                        oldextractedurls.append(tempurl + tempextractedurl)
                    elif extractedstart in ['href', 'HREF']:
                        if re.search(r'^https?:\/\/.*\/', url, re.I):
                            oldextractedurls.append(re.search(r'^(https?:\/\/.*)\/', url, re.I).group(1) + '/' + extractedurl)
                        else:
                            oldextractedurls.append(re.search(r'^(https?:\/\/.*)', url, re.I).group(1) + '/' + extractedurl)
                for extractedurl in re.findall(r'>[^<a-zA-Z0-9]*(https?:?//?[^<]+)<', response.text, re.I) + re.findall(r'\[[^<a-zA-Z0-9]*(https?:?//?[^\]]+)\]', response.text, re.I):
                    extractedurl = re.search(r'^([^#]*)', extractedurl).group(1)
                    oldextractedurls.append(extractedurl.replace(re.search(r'^(https?:?\/\/?)', extractedurl, re.I).group(1), re.search(r'^(https?)', extractedurl, re.I).group(1) + '://'))
                for extractedurl in oldextractedurls:
                    if '?' in extractedurl:
                        oldextractedurls.append(extractedurl.split('?')[0])
                for extractedurl in oldextractedurls:
                    if not re.search(r'^(https?:\/\/.*?) *$', extractedurl, re.I):
                        continue
                    extractedurl = extractedurl.replace('&amp;', '&').replace('\n', '').replace('\r', '').replace('\t', '')
                    extractedurl = re.search(r'^(https?:\/\/.*?) *$', extractedurl, re.I).group(1)
                    extractedurl = urllib.unquote(extractedurl)
                    try:
                        extractedurlpercent = re.search(r'^(https?://[^/]+).*$', extractedurl, re.I).group(1) + urllib.quote(re.search(r'^https?://[^/]+(.*)$', extractedurl, re.I).group(1).encode('utf8'), "!#$&'()*+,/:;=?@[]-._~")
                    except:
                        pass #bad url
                    for regex in regexes:
                        if re.search(regex, extractedurl, re.I) and not extractedurlpercent in extractedurls:
                            extractedurls.append(extractedurlpercent)
                            break
        return extractedurls
