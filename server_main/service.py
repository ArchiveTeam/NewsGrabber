import threading
import os
import shutil
import sys
import json
import time
import re

if os.path.isdir('services'):
    shutil.rmtree('services')
if not os.path.isdir('services'):
    os.makedirs('services')
if not os.path.isfile('services/__init__.py'):
    open('services/__init__.py', 'w').close()

import file
import services
import settings
import tools

reload(sys)
sys.setdefaultencoding("utf-8")


class RunServices(threading.Thread):

    """Services are here started and stopped."""

    def __init__(self):
        threading.Thread.__init__(self)
        self.services = []
        self.new_services = 0
        self.targets = file.File(settings.targets)
        self.discovery_files = {}

    def run(self):
        self.refresh_services()

    def refresh_services(self):
        if os.path.isdir('services'):
            shutil.rmtree('services')
        os.system('git clone https://github.com/ArchiveTeam/NewsGrabber.git')
        shutil.copytree(os.path.join('NewsGrabber', 'services'), 'services')
        shutil.rmtree('NewsGrabber')
        reload(services)
        self.start_services()

    def start_services(self):
        for file in [file for file in os.listdir('services') if file.startswith(
                'web__') and file.endswith('.py')]:
            service_name = file.replace('.py', '')
            if not service_name in self.services:
                self.new_services += 1
                self.services.append(service_name)
                settings.services[service_name] = Service(service_name)
                settings.services[service_name].daemon = True
                settings.services[service_name].start()
                settings.services[service_name].read_urls()
            settings.services[service_name].get_data()
        settings.irc_bot.send('PRIVMSG', 'Found {new_services} new services'.format(
            new_services=self.new_services), settings.irc_channel_bot)
        self.new_services = 0
        if not settings.get_urls:
            settings.get_urls = Urls()
            settings.get_urls.daemon = True
            settings.get_urls.start()
        self.distribute_services()

    def distribute_services(self):
        discovery_targets = self.get_discovery_targets()
        service_lists = tools.splitlist(self.services, len(discovery_targets))
        for i, target in enumerate(discovery_targets):
            filename = '{name}_services_list'.format(name=target['name'])
            self.discovery_files[i] = file.File(filename)
            filename_content = self.discovery_files[i].read_json()
            if isinstance(filename_content, dict):
                filename_content['services'] += service_lists[i]
            else:
                filename_content = {}
                filename_content['services'] = service_lists[i]
            filename_content['nick'] = target['name']
            self.discovery_files[i].write_json(filename_content)
        for target in discovery_targets:
            filename = '{name}_services_list'.format(name=target['name'])
            if os.path.isfile(filename):
                exit = os.system('rsync -avz --no-o --no-g --progress --remove-source-files {filename} {target}'.format(
                    filename=filename, target=target['rsync']))
                if exit != 0:
                    settings.irc_bot.send('PRIVMSG', 'Serviceslist {filename} failed to sync'.format(
                        **locals()), settings.irc_channel_bot)

    def stop(self):
        self.write_services()
        self.stop_grabs()

    def start_(self):
        self.start_grabs()

    def write_services(self):
        for key, value in settings.services.iteritems():
            value.write_urls()

    def get_website_service(self, website):
        stripped = lambda url: re.search(r'^(?:https?://)?(?:www\.)?([^/]+)', url, re.I).group(1)
        matching_services = []
        website = stripped(website)
        for key, value in settings.services.iteritems():
            website_service = stripped(value.service_urls[0])
            if website_service == website or '.' + website in website_service:
                matching_services.append(key)
        return matching_services

    def get_url_records(self, url, services, all_):
        def newfilter(url):
            def urlfilter(x):
                return x['url'].split('#')[0].endswith(url)
            return urlfilter

        stripped = lambda url: re.search(r'^(?:https?://)?(?:www\.)?([^#]+)', url, re.I).group(1)
        records = []
        url = stripped(url)
        customfilter = newfilter(url)
        if len(services) == 0:
            all_ = True
        matching = []
        if all_:
            for key, value in settings.services.iteritems():
                matching += list(filter(customfilter, value.service_log_urls))
        else:
            for key in services:
                matching += list(filter(customfilter, settings.services[key].service_log_urls))
        return matching

    def stop_grabs(self):
        settings.get_urls.running = False

    def start_grabs(self):
        settings.get_urls.running = True

    def get_discovery_targets(self):
        targets = self.targets.read_json()
        targets_ = []
        for target in targets.keys():
            if targets[target]['sort'] == 'discoverer':
                for i in range(targets[target]['quantity']):
                    targets_.append({'name': target,
                        'rsync': targets[target]['rsync']})
        return targets_


class Urls(threading.Thread):

    """In this class the new and old URLs are sorted and distributed."""

    def __init__(self):
        threading.Thread.__init__(self)
        self.url_lists = []
        self.url_count_new = 0
        self.url_count = 0
        self.urls_video = []
        self.urls_normal = []
        self.targets = file.File(settings.targets)
        self.grab_files = {}
        self.running = True

    def run(self):
        self.get_urls_new()

    def get_urls_new(self):
        runs = 0
        while True:
            for file_ in os.listdir(settings.dir_new_urllists):
                while not settings.get_urls_running:
                    time.sleep(1)
                urls_new_count = 0
                urls_new = json.load(open(os.path.join(
                    settings.dir_new_urllists, file_)))
                for url in urls_new:
                    if url['service'] in settings.services \
                          and not url in [u['url'] for u in \
                          settings.services[url['service']].service_log_urls]:
                        if not url['live']:
                            settings.services[url['service']].service_log_urls.append(
                                url)
                        self.add_url(url)
                        urls_new_count += 1
                    elif not url['service'] in settings.services \
                          and not url in self.urls_video + self.urls_normal:
                        self.add_url(url)
                        urls_new_count += 1
                self.count(urls_new_count)
                settings.logger.log('Loaded {urls} URL(s) from file {file}'.format(
                        urls=urls_new_count, file=file_))
                os.rename(os.path.join(settings.dir_new_urllists, file_),
                        os.path.join(settings.dir_old_urllists, file_))
            runs += 1
            if runs%15 == 0:
                self.report_urls()
            if runs == 60:
                self.distribute_urls()
                runs = 0
            time.sleep(60)

    def report_urls(self):
        settings.irc_bot.send('PRIVMSG', '{urls} URLs added in the last 15 minutes.'.format(
            urls=self.url_count_new), settings.irc_channel_bot)
        self.url_count_new = 0

    def distribute_urls(self):
        urls_video = list(self.urls_video)
        urls_normal = list(self.urls_normal)
        self.urls_video = list(self.urls_video[len(urls_video):])
        self.urls_normal = list(self.urls_normal[len(urls_normal):])
        urls_video_new = [url['url'] for url in urls_video]
        urls_video = list(urls_video_new)
        urls_normal_new = [url['url'] for url in urls_normal]
        urls_normal = list(urls_normal_new)
        lists = [{'sort': '-videos',
            'list': urls_video},
             {'sort': '',
             'list': urls_normal}]
        for list_ in lists:
            grab_targets = self.get_grab_targets()
            urls_lists = tools.splitlist(list_['list'], len(grab_targets))
            for i, target in enumerate(grab_targets):
                filename = '{name}{sort}_temp_{i}_{timestamp}'.format(
                    name=target['name'], sort=list_['sort'], i=i,
                    timestamp=time.time())
                self.grab_files[i] = file.File(filename)
                self.grab_files[i].write_json({'urls': urls_lists[i], 'nick': target['name']})
                exit = os.system('rsync -avz --no-o --no-g --progress --remove-source-files {filename} {target}'.format(
                    filename=filename, target=target['rsync']))
                if exit != 0:
                    settings.irc_bot.send('PRIVMSG', 'URLslist {filename} failed to sync.'.format(
                        **locals()), settings.irc_channel_bot)

    def count(self, i):
        self.url_count += i
        self.url_count_new += i

    def add_url(self, url):
        if url['sort'] == 'video':
            self.urls_video.append(url)
        elif url['sort'] == 'normal':
            self.urls_normal.append(url)

    def get_grab_targets(self):
        targets = self.targets.read_json()
        targets_ = []
        for target in targets.keys():
            if targets[target]['sort'] == 'grabber':
                for i in range(targets[target]['quantity']):
                    targets_.append({'name': target,
                        'rsync': targets[target]['rsync']})
        return targets_


class Service(threading.Thread):

    """This class is used to manage and run a service."""

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
        self.service_log_urls = []
        self.service_file_log_urls = file.File(os.path.join(settings.dir_donefiles, self.service_name))
        self.service_urls_age = time.time()

    def write_urls(self):
        self.service_file_log_urls.write_json(self.service_log_urls)

    def read_urls(self):
        service_log_urls = self.service_file_log_urls.read_json()
        if service_log_urls:
            self.service_log_urls = service_log_urls

    def dump_urls_age(self):
        if time.time() - self.service_urls_age >= settings.max_url_age:
            self.service_urls_age = time.time()

    def get_data(self):
        self.service_refresh = eval('services.{service_name}.refresh'.format(
            service_name=self.service_name))
        self.service_urls = eval('services.{service_name}.urls'.format(
            service_name=self.service_name))
        self.service_regex = eval('services.{service_name}.regex'.format(
            service_name=self.service_name))
        try:
            self.service_regex_video = eval('services.{service_name}.videoregex'.format(
                service_name=self.service_name))
        except:
            self.service_regex_video = None
        try:
            self.service_regex_live = eval('services.{service_name}.liveregex'.format(
                service_name=self.service_name))
        except:
            self.service_regex_live = None
        self.service_version = eval('services.{service_name}.version'.format(
            service_name=self.service_name))
        try:
            self.service_wikidata = eval('services.{service_name}.wikidata'.format(
                service_name=self.service_name))
        except:
            self.service_wikidata = None

    def get_new_url(self, url):
        if not url in self.service_log_urls:
            self.service_log_urls.append(url)