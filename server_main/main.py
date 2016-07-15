import settings
import os
import service
import threading
import irc
import log


def main():
    settings.init()
    settings.logger = log.Log(settings.log_file_name)
    settings.logger.daemon = True
    settings.logger.start()
    settings.logger.log('Starting NewsGrabber')

    if not os.path.isdir(settings.dir_new_urllists):
        os.makedirs(settings.dir_new_urllists)
        settings.logger.log("Created directory '{dir_new_urllists}'".format(
                dir_new_urllists=settings.dir_new_urllists))
    if not os.path.isdir(settings.dir_old_urllists):
        os.makedirs(settings.dir_old_urllists)
        settings.logger.log("Created directory '{dir_old_urllists}'".format(
                dir_old_urllists=settings.dir_old_urllists))
    if not os.path.isdir(settings.dir_donefiles):
        os.makedirs(settings.dir_donefiles)
        settings.logger.log("Created directory '{dir_donefiles}'".format(
                dir_donefiles=settings.dir_donefiles))
    if not os.path.isfile('rsync_targets'):
        settings.logger.log("Please add one or more rsync targets to file 'rsync_targets'", 'ERROR')
    if not os.path.isfile('rsync_targets_discovery'):
        settings.logger.log("Please add one or more discovery rsync targets to file 'rsync_targets_discovery'", 'ERROR')

    settings.irc_bot = irc.IRC()
    settings.irc_bot.daemon = True
    settings.irc_bot.start()
    settings.run_services = service.RunServices()
    settings.run_services.daemon = True
    settings.run_services.start()
    settings.get_urls = service.Urls()
    settings.get_urls.daemon = True
    settings.get_urls.start()
    
    while True:
        pass

if __name__ == '__main__':
    main()
