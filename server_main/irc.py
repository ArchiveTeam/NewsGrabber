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
        if command[0] == '!help':
            self.send('PRIVMSG', 'Hello! My options are:', user)
            self.send('PRIVMSG', "'!EMERGENCY_STOP': Stop the grab immediatly.", user)
            self.send('PRIVMSG', "'!stop': Write lists of URLs, finish current running grabs and not start new grabs.",
                    user)
            self.send('PRIVMSG', "'!writefiles': Write lists of URLs.", user)
            self.send('PRIVMSG', "'!imgrab', '!immediate-grab' or '!immediate_grab': Make sure URLs are grabbed immediatly after they\'re found. Add \'remove\', \'rem\' or \'r\' to stop URLs from being grabbed immediatly after they\'re found.",
                    user)
            self.send('PRIVMSG', "'!info' or '!information': Request information about a service.",
                    user)
            self.send('PRIVMSG', "'!upload': Upload the WARC files.", user)
        elif command[0] == '!stop':
            self.send('PRIVMSG', '{user}: Stopping...'.format(user=user), channel)
            settings.run_services.stop()
            self.send('PRIVMSG', '{user}: Stopped.'.format(user=user), channel)
            settings.running = False
        elif command[0] == '!pause':
            if (len(command) == 2 and command[1] == 'global') or len(command) == 1:
                settings.get_urls_running = False
                settings.upload_running = False
                self.send('PRIVMSG', '{user}: No new URLs will be sorted or uploads started.'.format(
                        user=user), channel)
        elif command[0] == '!resume':
            if (len(command) == 2 and command[1] == 'global') or len(command) == 1:
                settings.get_urls_running = False
                settings.upload_running = False
                self.send('PRIVMSG', '{user}: New URLs will be sorted or uploads started.'.format(
                        user=user), channel)
        elif command[0] == '!pause-urls':
            settings.get_urls_running = False
            self.send('PRIVMSG', '{user}: No new URLs will be sorted.'.format(
                    user=user), channel)
        elif command[0] == '!resume-urls':
            settings.get_urls_running = True
            self.send('PRIVMSG', '{user}: New URLs will be sorted.'.format(
                    user=user), channel)
        elif command[0] == '!pause-upload':
            if (len(command) == 2 and command[1] == 'global') or len(command) == 1:
                settings.upload_running = True
                self.send('PRIVMSG', '{user}: No new upload will be started.'.format(
                        user=user), channel)
        elif command[0] == '!resume-upload':
            if (len(command) == 2 and command[1] == 'global') or len(command) == 1:
                settings.upload_running = False
                self.send('PRIVMSG', '{user}: New upload will be started.'.format(
                        user=user), channel)
        elif command[0] == '!version':
            if len(command) == 1 or (len(command) == 2 and command[1] == 'global'):
                self.send('PRIVMSG', '{user}: Version is {version}.'.format(
                        user=user, version=settings.version), channel)
        elif command[0] == '!writefiles':
            self.send('PRIVMSG', '{user}: Writing URLs...'.format(user=user), channel)
            settings.run_services.write_services()
            settings.upload.write()
            self.send('PRIVMSG', '{user}: Written URLs.'.format(user=user), channel)
        elif command[0] == '!EMERGENCY_STOP':
            if (len(command) == 2 and command[1] == 'global') or len(command) == 1:
                self.send('PRIVMSG', '{user}: ABORTING.'.format(user=user), channel)
                settings.running = False
        elif command[0] in ('!cu', '!con-uploads', '!concurrent-uploads'):
            if len(command) == 2 and command[1].isdigit():
                settings.max_concurrent_uploads = int(command[1])
        elif command[0] in ('!rs', '!refresh-services'):
            self.send('PRIVMSG', '{user}: Refreshing services...'.format(user=user),
                    channel)
            settings.run_services.refresh_services()
            self.send('PRIVMSG', '{user}: Refreshed services.'.format(user=user),
                    channel)
        elif command[0] in ('!info', '!information'):
            if len(command) == 1:
                self.send('PRIVMSG', '{user}: Please specify a service or website.'.format(
                        user=user), channel)
            elif command[1].startswith('web__'):
                if command[1] in settings.services:
                    service_name = settings.services[command[1]].service_name
                    service_refresh = settings.services[command[1]].service_refresh
                    service_urls = settings.services[command[1]].service_urls
                    service_regex = str(settings.services[command[1]].service_regex).replace('\\\\', '\\')
                    service_regex_video = str(settings.services[command[1]].service_regex_video).replace('\\\\', '\\')
                    service_regex_live = str(settings.services[command[1]].service_regex_live).replace('\\\\', '\\')
                    service_version = settings.services[command[1]].service_version
                    service_wikidata = settings.services[command[1]].service_wikidata
                    service_log_urls = settings.services[command[1]].service_log_urls
                    self.send('PRIVMSG', '{user}: Details for service {service}:'.format(
                            user=user, service=service_name), channel)
                    self.send('PRIVMSG', '{user}: Service version is {version}.'.format(
                            user=user, version=service_version), channel)
                    self.send('PRIVMSG', '{user}: Refresh time is {refresh} seconds.'.format(
                            user=user, refresh=service_refresh), channel)
                    s = 's' if len(service_urls) != 1 else ''
                    self.send('PRIVMSG', '{user}: {i} seed URL{s}: {urls}.'.format(
                            user=user, i=len(service_urls), s=s, urls=', '.join(service_urls)),
                            channel)
                    self.send('PRIVMSG', '{user}: Grabbing URLs matching {regex}.'.format(
                            user=user, regex=service_regex), channel)
                    if service_regex_video != '[]':
                        self.send('PRIVMSG', '{user}: Video URLs match {regex}.'.format(
                                user=user, regex=service_regex_video), channel)
                    if service_regex_live != '[]':
                        self.send('PRIVMSG', '{user}: Live URLs match {regex}.'.format(
                                user=user, regex=service_regex_live), channel)
                    if service_wikidata:
                        self.send('PRIVMSG', '{user}: Wikidata ID is .'.format(
                                user=user, regex=str(service_wikidata)), channel)
                    s = 's' if len(service_log_urls) != 1 else ''
                    self.send('PRIVMSG', '{user}: {i} URL{s} grabbed so far.'.format(
                            user=user, i=len(service_log_urls), s=s), channel)
                else:
                    self.send('PRIVMSG', 'This service does not exist.'.format(
                            user=user), channel)
            else:
                corresponding_services = settings.run_services.get_website_service(command[1])
                if len(corresponding_services) > 0:
                    self.send('PRIVMSG', '{user}: Corresponding services are {services}'.format(
                            user=user, services=', '.join(corresponding_services)), channel)
                    self.send('PRIVMSG', "{user}: Use '!info <service>' to get more information.".format(
                            user=user), channel)
                else:
                    self.send('PRIVMSG', '{user}: No corresponding services found.'.format(
                            user=user), channel)
