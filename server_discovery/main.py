import settings
import os
import service
import time
import irc
import log
import tools


def main():
    settings.init()
    settings.logger = log.Log(settings.log_file_name)
    settings.logger.daemon = True
    settings.logger.start()
    settings.logger.log('Starting NewsGrabber')

    tools.create_dir(settings.dir_assigned_services)

    if not os.path.isfile(settings.target):
        settings.logger.log("Please add one or more discovery rsync targets to file 'rsync_targets_discovery'", 'ERROR')

    settings.irc_bot = irc.IRC()
    settings.irc_bot.daemon = True
    settings.irc_bot.start()
    time.sleep(1)
    settings.upload = service.Upload()
    settings.upload.daemon = True
    settings.upload.start()
    settings.run_services = service.RunServices()
    settings.run_services.daemon = True
    settings.run_services.start()
    
    while settings.running:
        time.sleep(1)

if __name__ == '__main__':
    main()
