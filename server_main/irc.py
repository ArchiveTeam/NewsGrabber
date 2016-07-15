import socket
import file
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
        self.send('JOIN', '{channel_main}'.format(
                channel_main=self.channel_main))
        self.send('JOIN', '{channel_bot}'.format(
                channel_bot=self.channel_bot))
        self.send('PRIVMSG', "Hello! I've just been (re)started. Follow my"
                " newsgrabs in {channel_bot}".format(channel_bot=self.channel_bot),
                self.channel_main)
        self.send('PRIVMSG', 'Hello!', self.channel_bot)
        self.send('PRIVMSG', 'Version {version}.'.format(version=settings.version),
                self.channel_bot)

        self.listener()
        
    def send(self, command, string, channel=''):
        message = '{command} {string}'.format(command=command, string=string)
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
            settings.logger.log('IRC - {message}'.format(message=message))
            if message.startswith('PING :'):
                message_new = re.search(r'^[^:]+:(.*)$', message).group(1)
                self.send('PONG', ':{new}'.format(new=new_message))
            elif re.search(r'^:.+PRIVMSG[^:]+:!.*', message):
                command = re.search(r'^:.+PRIVMSG[^:]+:(!.*)', message).group(1).strip().split(' ')
                user = re.search(r'^:([^!]+)!', message).group(1)
                channel = re.search(r'^:[^#]+(#[^ :]+) ?:', irc_message).group(1)
                self.commands_received.append({'command': command, 'user': user, 'channel': channel})
                self.command(command, user)

    def command(self, command, user):
        if command == '!help':
            pass
        elif command == '!stop':
            pass
        elif command == '!start':
            pass
        elif command == '!version':
            pass
        elif command == '!writefiles':
            pass
        elif command == '!upload':
            pass
        elif command == '!EMERGENCY_STOP':
            pass
        elif command in ('!cu', '!con-uploads', '!concurrent-uploads'):
            pass
        elif command in ('!rs', '!refresh-services'):
            pass
        elif command in ('!info', '!information'):
            pass
