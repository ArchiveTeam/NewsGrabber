import os
import time

import tools
import log
import settings
import irc
import grab
import upload

def main():
    settings.init()
    settings.logger = log.Log(settings.log_file_name)
    settings.logger.daemon = True
    settings.logger.start()
    settings.logger.log('Starting grabber {name}'.format(
            name=settings.irc_nick))

    tools.create_dir(settings.dir_ready)
    tools.create_dir(settings.dir_new_lists)
    tools.create_dir(settings.dir_old_lists)

    if not os.path.isfile(settings.target_main):
        raise Exception("Please add a rsync target to file '{name}'.".format(
            name=settings.target_main))

    settings.irc_bot = irc.IRC()
    settings.irc_bot.daemon = True
    settings.irc_bot.start()
    time.sleep(30)
    settings.upload = upload.Upload()
    settings.upload.daemon = True
    settings.upload.start()
    settings.grab = grab.Grab()
    settings.grab.daemon = True
    settings.grab.start()

    while settings.running:
    #    if not settings.logger.isAlive():
    #        print('The logger stopped running...')
    #        settings.irc_bot.send('PRIVMSG', 'The logger stopped running...',
    #                settings.irc_channel_bot)
    #        settings.running = False
    #    if not settings.irc_bot.isAlive():
    #        print('The IRC bot stopped running...')
    #        settings.running = False
    #    if not settings.upload.isAlive():
    #        print('The uploader stopped running...')
    #        settings.irc_bot.send('PRIVMSG', 'The uploader stopped running...',
    #                settings.irc_channel_bot)
    #        settings.running = False
    #    if not settings.grab.isAlive():
    #        print('The grabber stopped running...')
    #        settings.irc_bot.send('PRIVMSG', 'The grabber stopped working...',
    #                settings.irc_channel_bot)
    #        settings.running = False
        time.sleep(1)

if __name__ == '__main__':
    main()