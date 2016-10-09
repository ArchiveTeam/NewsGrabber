import socket
import threading
import re

import psutil

import service
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
        self.send('NICK', self.nick)
        self.send('JOIN', self.channel_bot)
        self.send('PRIVMSG', 'Hello!', self.channel_bot)
        self.send('PRIVMSG', 'Version {version}.'
                .format(version=settings.version), self.channel_bot)

        self.listener()

    def set_nick(self, nick):
        settings.irc_nick = nick
        self.nick = nick
        self.send('NICK', nick)
        
    def send(self, command, string, channel=''):
        if channel != '':
            channel += ' :'
        message = '{command} {channel}{string}'.format(**locals())
        try:
            settings.logger.log('IRC - {message}'.format(**locals()))
            self.messages_sent.append(message)
            self.server.send('{message}\n'.format(**locals()))
        except Exception as exception:
            settings.logger.log('{exception}'.format(**locals()),
                    'WARNING')
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
        names = (settings.irc_nick, 'global', 'discovery', 'disco',
            'discoverer')
        check_name = lambda command: len(command) != 1 and command[1] in names
        if command[0] == '!status':
            self.send('PRIVMSG', "{user}: Discoverer is running."
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
        elif command[0] in ('!imgrab', '!immediate-grab') \
              and check_name(command):
            if command[1] in settings.services:
                settings.services[command[1]].immediate_grab = True
                self.send('PRIVMSG', '{user}: Discovered URLs for service '
                    '{command[1]} will be grabbed immediatly.'.format(
                    **locals()), channel)
        elif command[0] in ('!imgrab-remove', '!immediate-grab-remove') \
              and  check_name(command):
            if command[1] in settings.services:
                settings.services[command[1]].immediate_grab = False
                self.send('PRIVMSG', '{user}: Discovered URLs for service '
                    '{command[1]} will not be grabbed immediatly.'
                    .format(**locals()), channel)
        elif command[0] == '!clear' and check_name(command):
            settings.run_services.clear()
            self.send('PRIVMSG', '{user}: Cleared lists.')
        elif command[0] == '!version' and check_name(command):
            self.send('PRIVMSG', '{user}: Version is {version}.'
                .format(user=user, version=settings.version), channel)
        elif command[0] == '!pause' and check_name(command):
            settings.run_services_running = False
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: No new grabs or uploads will be '
                'started.'.format(**locals()), channel)
        elif command[0] == '!resume' and check_name(command):
            settings.run_services_running = True
            settings.upload_running = True
            self.send('PRIVMSG', '{user}: New grabs or uploads will be '
                'started.'.format(**locals()), channel)
        elif command[0] == '!pause-upload' and check_name(command):
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: No new uploads will be started.'
                .format(**locals()), channel)
        elif command[0] == '!resume-upload' and check_name(command):
            settings.upload_running = True
            self.send('PRIVMSG', '{user}: New uploads will be started.'
                .format(**locals()), channel)
        elif command[0] == '!pause-grab' and check_name(command):
            settings.run_services_running = False
            self.send('PRIVMSG', '{user}: No new grabs will be started.'
                .format(**locals()), channel)
        elif command[0] == '!resume-grab' and check_name(command):
            settings.run_services_running = True
            self.send('PRIVMSG', '{user}: New grabs will be started.'
                .format(**locals()), channel)
        elif command[0] == '!refresh' and len(command) == 3 \
              and check_name(command):
            if command[2].isdigit():
                service.Service.global_refresh = int(command[2])
                self.send('PRIVMSG', '{user}: Set refresh to {refresh} '
                    'seconds.'
                    .format(user=user, refresh=command[2]), channel)
            elif command[2] == 'default':
                service.Service.global_refresh = None
                self.send('PRIVMSG', '{user}: Set refresh back to services '
                    'defaults.'
                    .format(user=user, refresh=command[2]), channel)
        elif command[0] == '!stop' and check_name(command):
            self.send('PRIVMSG', '{user}: Stopping...'
                .format(**locals()), channel)
            settings.running = False
        elif command[0] in ('!info', '!information') and len(command) == 2:
            if command[1] in settings.services:
                self.send('PRIVMSG', '{user}: Running this service.'
                    .format(**locals()), channel)