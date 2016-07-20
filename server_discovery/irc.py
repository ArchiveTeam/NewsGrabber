import socket
import settings
import threading
import re


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

        self.send('USER', '{nick} {nick} {nick} :This is the bot for'
                ' {channel_main}. https://github.com/ArchiveTeam/NewsGrabber.'
                .format(nick=self.nick, channel_main=self.channel_main))
        self.send('NICK', '{nick}'.format(nick=self.nick))
        self.send('JOIN', '{channel_bot}'.format(
                channel_bot=self.channel_bot))
        self.send('PRIVMSG', 'Hello!', self.channel_bot)
        self.send('PRIVMSG', 'Version {version}.'.format(version=settings.version),
                self.channel_bot)

        self.listener()
        
    def send(self, command, string, channel=''):
        if channel != '':
            channel += ' :'
        message = '{command} {channel}{string}'.format(command=command,
                channel=channel, string=string)
        try:
            settings.logger.log('IRC - {message}'.format(message=message))
            self.messages_sent.append(message)
            self.server.send('{message}\n'.format(message=message))
        except Exception as exception:
            settings.logger.log('{exception}'.format(exception=exception),
                    'WARNING')
            self.connect()
            self.server.send('{message}\n'.format(message=message))

    def listener(self):
        while True:
            message = self.server.recv(2048)
            self.messages_received.append(message)
            for line in message.splitlines():
                settings.logger.log('IRC - {message}'.format(message=line))
            if message.startswith('PING :'):
                message_new = re.search(r'^[^:]+:(.*)$', message).group(1)
                self.send('PONG', ':{new}'.format(new=message_new))
            elif re.search(r'^:.+PRIVMSG[^:]+:!.*', message):
                command = re.search(r'^:.+PRIVMSG[^:]+:(!.*)', message).group(1).strip().split(' ')
                command = [s.strip() for s in command if len(s.strip()) != 0]
                user = re.search(r'^:([^!]+)!', message).group(1)
                channel = re.search(r'^:[^#]+(#[^ :]+) ?:', message).group(1)
                self.commands_received.append({'command': command, 'user': user,
                                               'channel': channel})
                self.command(command, user, channel)

    def command(self, command, user, channel):
        names = (settings.irc_nick, 'global', 'discovery', 'disco', 'discoverer')
        if command[0] == '!status':
            self.send('PRIVMSG', "{user}: Discoverer is running.".format(user=user), channel)
        elif command[0] == '!version' and len(command) != 1 and command[1] in names:
            self.send('PRIVMSG', '{user}: Version is {version}.'.format(
                    user=user, version=settings.version), channel)
        elif command[0] == '!pause' and len(command) != 1 and command[1] in names:
            settings.run_services_running = False
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: No new grabs or uploads will be started.'.format(user=user), channel)
        elif command[0] == '!pause-upload' and len(command) != 1 and command[1] in names:
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: No new uploads will be started.'.format(user=user), channel)
        elif command[0] == '!resume-upload' and len(command) != 1 and command[1] in names:
            settings.upload_running = False
            self.send('PRIVMSG', '{user}: New uploads will be started.'.format(user=user), channel)
        elif command[0] == '!pause-grab' and len(command) != 1 and command[1] in names:
            settings.run_services_running = False
            self.send('PRIVMSG', '{user}: No new grabs will be started.'.format(user=user), channel)
        elif command[0] == '!resume-grab' and len(command) != 1 and command[1] in names:
            settings.run_services_running = False
            self.send('PRIVMSG', '{user}: New grabs will be started.'.format(user=user), channel)
        elif command[0] == '!resume' and len(command) != 1 and command[1] in names:
            settings.run_services_running = True
            settings.upload_running = True
            self.send('PRIVMSG', '{user}: New grabs or uploads will be started.'.format(user=user), channel)
        elif command[0] == '!EMERGENCY_STOP' and len(command) != 1 and command[1] in names:
            self.send('PRIVMSG', '{user}: ABORTING.'.format(user=user), channel)
            settings.running = False
        elif command[0] in ('!info', '!information') and len(command) == 2:
            if command[1] in settings.services:
                self.send('PRIVMSG', '{user}: Running this service.'.format(user=user),
                        channel)
