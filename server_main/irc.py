import socket
import datetime
import threading
import re

import pytz

import settings


class IRC(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.channel_bot = settings.irc_channel_bot
        self.channel_main = settings.irc_channel_main
        self.nick = settings.irc_nick
        self.server_name = settings.irc_server_name
        self.server_port = settings.irc_server_port
        self.server = None
        self.messages_received = []
        self.messages_sent = []
        self.commands_received = []
        self.commands_sent = []

    def run(self):
        self.connect()

    def connect(self):
        if self.server:
            self.server.close()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.server_name, self.server_port))

        self.send('USER', '{nick} {nick} {nick} :This is the bot for '
            '{channel_main}. '
            'https://github.com/ArchiveTeam/NewsGrabber.'
            .format(nick=self.nick, channel_main=self.channel_main))
        self.send('NICK', '{nick}'.format(nick=self.nick))
        self.send('JOIN', '{channel_main}'.format(
            channel_main=self.channel_main))
        self.send('JOIN', '{channel_bot}'.format(
            channel_bot=self.channel_bot))
        self.send('PRIVMSG', "Hello! I've just been (re)started. Follow my "
            "newsgrabs in {channel_bot}"
            .format(channel_bot=self.channel_bot), self.channel_main)
        self.send('PRIVMSG', 'Hello!', self.channel_bot)
        self.send('PRIVMSG', 'Version {version}.'
            .format(version=settings.version), self.channel_bot)

        self.listener()
        
    def send(self, command, string, channel=''):
        if channel != '':
            channel += ' :'
        message = '{command} {channel}{string}'.format(**locals())
        try:
            settings.logger.log('IRC - {message}'.format(**locals()))
            self.messages_sent.append(message)
            self.server.send('{message}\n'.format(**locals()))
        except Exception as exception:
            settings.logger.log('{exception}'.format(**locals()), 'WARNING')
            self.connect()
            self.server.send('{message}\n'.format(**locals()))

    def listener(self):
        while True:
            message = self.server.recv(2048)
            self.messages_received.append(message)
            for line in message.splitlines():
                settings.logger.log('IRC - {line}'.format(**locals()))
            if message.startswith('PING :'):
                message_new = re.search(r'^[^:]+:(.*)$', message).group(1)
                self.send('PONG', ':{message_new}'.format(**locals()))
            elif re.search(r'^:.+PRIVMSG[^:]+:!.*', message):
                command = re.search(r'^:.+PRIVMSG[^:]+:(!.*)', message) \
                    .group(1).strip().split(' ')
                command = [s.strip() for s in command if len(s.strip()) != 0]
                user = re.search(r'^:([^!]+)!', message).group(1)
                channel = re.search(r'^:[^#]+(#[^ :]+) ?:', message).group(1)
                self.commands_received.append({'command': command,
                    'user': user,
                    'channel': channel})
                self.command(command, user, channel)

    def command(self, command, user, channel):
        names = (settings.irc_nick, 'global', 'main', 'storage')
        check_name = lambda command: len(command) != 1 and command[1] in names
        if command[0] == '!help':
            self.send('PRIVMSG', '{user}: For IRC commands for the main '
                'server: https://github.com/ArchiveTeam/NewsGrabber/blob/'
                'master/server_main/README.md'
                .format(**locals()), channel)
            self.send('PRIVMSG', '{user}: For IRC commands for the discovery '
                'server: https://github.com/ArchiveTeam/NewsGrabber/blob/'
                'master/server_discovery/README.md'
                .format(**locals()), channel)
            self.send('PRIVMSG', '{user}: For IRC commands for the grab '
                'server: https://github.com/ArchiveTeam/NewsGrabber/blob/'
                'master/server_grab/README.md'
                .format(**locals()), channel)
        elif command[0] == '!server-stats' and check_name(command):
            self.send('PRIVMSG', '{user}: Getting server stats...'
                .format(**locals()), channel)
            disk_usage = psutil.disk_usage('.')
            cpu_percent = psutil.cpu_percent(interval=5)
            cpu_times_percent = psutil.cpu_times_percent(interval=5)
            virtual_memory = psutil.virtual_memory()
            self.send('PRIVMSG', '{user}: CPU usage percent: '
                'total {cpu_percent} - '
                'user {cpu_times_percent.user} - '
                'nice {cpu_times_percent.nice} - '
                'system {cpu_times_percent.system} - '
                'idle {cpu_times_percent.idle}.'.format(**locals()), channel)
            self.send('PRIVMSG', '{user}: Virtual memory usage: '
                'total {virtual_memory.total} - '
                'percent {virtual_memory.percent}.'
                .format(**locals()), channel)
            self.send('PRIVMSG', '{user}: Disk usage: '
                'total {disk_usage.total} - '
                'percent {disk_usage.percent}.'.format(**locals()), channel)
        elif command[0] == '!handle-targets':
            self.send('PRIVMSG', '{user}: ')
        elif command[0] == '!stop' and check_name(command):
            self.send('PRIVMSG', '{user}: Stopping...'
                .format(**locals()), channel)
            settings.run_services.stop()
            self.send('PRIVMSG', '{user}: Stopped.'
                .format(**locals()), channel)
            settings.running = False
        elif command[0] == '!pause' and check_name(command):
            settings.get_urls_running = False
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: No new URLs will be sorted or '
                'uploads started.'.format(**locals()), channel)
        elif command[0] == '!resume' and check_name(command):
            settings.get_urls_running = False
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: New URLs will be sorted or uploads '
                'started.'.format(**locals()), channel)
        elif command[0] == '!pause-urls':
            settings.get_urls_running = False
            self.send('PRIVMSG', '{user}: No new URLs will be sorted.'
                .format(**locals()), channel)
        elif command[0] == '!resume-urls':
            settings.get_urls_running = True
            self.send('PRIVMSG', '{user}: New URLs will be sorted.'
                .format(**locals()), channel)
        elif command[0] == '!pause-upload' and check_name(command):
            settings.upload_running = True
            self.send('PRIVMSG', '{user}: No new upload will be started.'
                .format(**locals()), channel)
        elif command[0] == '!resume-upload' and check_name(command):
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: New upload will be started.'
                .format(**locals()), channel)
        elif command[0] == '!version' and check_name(command):
            self.send('PRIVMSG', '{user}: Version is {version}.'
                .format(user=user, version=settings.version), channel)
        elif command[0] == '!writefiles':
            self.send('PRIVMSG', '{user}: Writing URLs...'
                .format(**locals()), channel)
            settings.run_services.write_services()
            settings.upload.write()
            self.send('PRIVMSG', '{user}: Written URLs.'
                .format(**locals()), channel)
        elif command[0] == '!EMERGENCY_STOP' and check_name(command):
            self.send('PRIVMSG', '{user}: ABORTING.'
                .format(**locals()), channel)
            settings.running = False
        elif command[0] in ('!cu', '!con-uploads', '!concurrent-uploads') \
              and check_name(command):
            if len(command) == 2 and command[1].isdigit():
                settings.max_concurrent_uploads = int(command[1])
        elif command[0] in ('!rs', '!refresh-services'):
            self.send('PRIVMSG', '{user}: Refreshing services...'
                .format(**locals()), channel)
            settings.run_services.refresh_services()
            self.send('PRIVMSG', '{user}: Refreshed services.'
                .format(**locals()), channel)
        elif command[0] in ('!info', '!information'):
            if len(command) == 1:
                self.send('PRIVMSG', '{user}: Please specify a service or '
                    'website.'.format(**locals()), channel)
            elif command[1].startswith('web__'):
                if command[1] in settings.services:
                    service_name = settings.services[command[1]].service_name
                    service_refresh = \
                        settings.services[command[1]].service_refresh
                    service_urls = settings.services[command[1]].service_urls
                    service_regex = \
                        str(settings.services[command[1]].service_regex) \
                        .replace('\\\\', '\\')
                    service_regex_video = \
                        str(settings.services[command[1]].service_regex_video) \
                        .replace('\\\\', '\\')
                    service_regex_live = \
                        str(settings.services[command[1]].service_regex_live) \
                        .replace('\\\\', '\\')
                    service_version = \
                        settings.services[command[1]].service_version
                    service_wikidata = \
                        settings.services[command[1]].service_wikidata
                    service_log_urls = \
                        settings.services[command[1]].service_log_urls
                    self.send('PRIVMSG', '{user}: Details for service '
                        '{service_name}:'.format(**locals()), channel)
                    self.send('PRIVMSG', '{user}: Service version is '
                        '{service_version}.'.format(**locals()), channel)
                    self.send('PRIVMSG', '{user}: Refresh time is '
                        '{service_refresh} seconds.'
                        .format(**locals()), channel)
                    s = 's' if len(service_urls) != 1 else ''
                    self.send('PRIVMSG', '{user}: {i} seed URL{s}: {urls}.'
                        .format(user=user, i=len(service_urls), s=s,
                        urls=', '.join(service_urls)), channel)
                    self.send('PRIVMSG', '{user}: Grabbing URLs matching '
                        '{service_regex}.'.format(**locals()), channel)
                    if service_regex_video != '[]':
                        self.send('PRIVMSG', '{user}: Video URLs match '
                            '{service_regex_video}.'
                            .format(**locals()), channel)
                    if service_regex_live != '[]':
                        self.send('PRIVMSG', '{user}: Live URLs match '
                            '{service_regex_live}.'
                            .format(**locals()), channel)
                    if service_wikidata:
                        self.send('PRIVMSG', '{user}: Wikidata ID is .'
                            .format(**locals()), channel)
                    s = 's' if len(service_log_urls) != 1 else ''
                    self.send('PRIVMSG', '{user}: {i} URL{s} grabbed so far.'
                        .format(user=user, i=len(service_log_urls), s=s),
                        channel)
                else:
                    self.send('PRIVMSG', 'This service does not exist.'
                        .format(**locals()), channel)
            else:
                all_ = False
                if len(command) == 3 and command[2] == 'all':
                    all_ = True
                corresponding_services = \
                    settings.run_services.get_website_service(command[1])
                corresponding_services_num = len(corresponding_services)
                records = \
                    settings.run_services.get_url_records(command[1],
                    corresponding_services, all_)
                records_num = len(records)
                if corresponding_services_num > 0:
                    is_are = 'is' if corresponding_services_num == 1 \
                        else 'are'
                    self.send('PRIVMSG', '{user}: Corresponding service '
                        '{is_are} {services}.'
                        .format(user=user, 
                        services=', '.join(corresponding_services)),
                        channel)
                    self.send('PRIVMSG', "{user}: Use '!info <service>' to "
                        "get more information about a service."
                        .format(**locals()), channel)
                else:
                    self.send('PRIVMSG', '{user}: No corresponding services '
                        'found.'.format(**locals()), channel)
                if records_num > 0:
                    s = '' if records_num == 1 else 's'
                    self.send('PRIVMSG', '{user}: This URL is grabbed '
                        '{records_num} time{s}.'.format(**locals()), channel)
                    if records_num > 1:
                        low = None
                        for record in records:
                            if not low or record['time'] < low[0]:
                                low = (0, record)
                        records[0] = low[1]
                        self.send('PRIVMSG', '{user}: Info of first time URL '
                            'was found:'.format(**locals()), channel)
                    self.send('PRIVMSG', '{user}: URL found on {a}.'
                        .format(user=user,
                        a=pytz.utc.localize(datetime.datetime
                        .utcfromtimestamp(records[0]['time']))
                        .strftime('%Y-%m-%d %H:%M:%S %Z')), channel)
                    self.send('PRIVMSG', '{user}: URL found by bot {a}.'
                        .format(user=user, a=records[0]['bot_nick']), channel)
                    self.send('PRIVMSG', '{user}: URL found with service {a}.'
                        .format(user=user, a=records[0]['service']), channel)
                    self.send('PRIVMSG', '{user}: URL found with service URL '
                        '{a}.'
                        .format(user=user, a=records[0]['service_url']),
                        channel)
                    self.send('PRIVMSG', '{user}: URL found with service '
                        'version {a}.'.format(user=user,
                        a=records[0]['service_version']), channel)
                    self.send('PRIVMSG', '{user}: URL found with script '
                        'version {a}.'
                        .format(user=user, a=records[0]['script_version']),
                        channel)
                    self.send('PRIVMSG', '{user}: This URL is a {a} URL.'
                        .format(user=user, a=records[0]['sort']), channel)
                    if records[0]['live']:
                        self.send('PRIVMSG', '{user}: This URL is a live-URL.'
                            .format(user=user, a=records[0]['service']),
                            channel)
                    if records[0]['immediate_grab']:
                        self.send('PRIVMSG', '{user}: This URL is grabbed '
                            'immediatly.'
                            .format(user=user, a=records[0]['service']),
                            channel)