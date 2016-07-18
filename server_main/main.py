import settings
import os
import service
import threading
import time
import irc
import log
import upload
import tools


def main():
    settings.init()
    settings.logger = log.Log(settings.log_file_name)
    settings.logger.daemon = True
    settings.logger.start()
    settings.logger.log('Starting NewsGrabber')

    tools.create_dir(settings.dir_new_urllists)
    tools.create_dir(settings.dir_old_urllists)
    tools.create_dir(settings.dir_donefiles)
    tools.create_dir(settings.dir_ready)
    tools.create_dir(settings.dir_last_upload)

    if not os.path.isfile('rsync_targets'):
        settings.logger.log("Please add one or more rsync targets to file 'rsync_targets'", 'ERROR')
    if not os.path.isfile('rsync_targets_discovery'):
        settings.logger.log("Please add one or more discovery rsync targets to file 'rsync_targets_discovery'", 'ERROR')

    settings.irc_bot = irc.IRC()
    settings.irc_bot.daemon = True
    settings.irc_bot.start()
    settings.upload = upload.Upload()
    settings.upload.daemon = True
    settings.upload.start()
    settings.run_services = service.RunServices()
    settings.run_services.daemon = True
    settings.run_services.start()
    
    while settings.running:
        time.sleep(1)

if __name__ == '__main__':
    main()
