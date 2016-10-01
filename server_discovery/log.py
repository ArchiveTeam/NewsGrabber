import datetime
import threading

import settings
import file


class Log(threading.Thread):
    def __init__(self, file_name):
        threading.Thread.__init__(self)
        self.file_name = file_name
        self.file = file.File(self.file_name)

    def log(self, strings, priority='INFO'):
        time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        for string in [string.strip() for string in strings.strip().splitlines()]:
            message = '[{time}] {version} - {priority} - {string}'.format(
                    time=time, priority=priority, version=settings.version,
                    string=string)
            self.file.append('{message}\n'.format(message=message))
            if priority == 'ERROR':
                settings.irc_bot.send('PRIVMSG',
                        'I just crashed. See the log for more information.',
                        settings.irc_channel_main)
                settings.irc_bot.send('PRIVMSG',
                        'I just crashed. See the log for more information.',
                        settings.irc_channel_bot)
                raise Exception(string)
            print(message.strip())
