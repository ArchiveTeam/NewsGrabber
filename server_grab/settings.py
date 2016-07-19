def init():
    global version
    global irc_channel_bot
    global irc_channel_main
    global irc_nick
    global irc_server_name
    global irc_server_port
    global dir_ready
    global dir_new_lists
    global dir_old_lists
    global max_concurrent_uploads
    global target_main
    global log_file_name
    global running
    global logger
    global irc_bot
    global grab_running
    global upload_running
    global grab
    global upload

    version = 20160719.01
    irc_channel_bot = '#newsgbot'
    irc_channel_main = '#newsg'
    irc_nick = 'newsbud'
    irc_server_name = 'irc.underworld.no'
    irc_server_port = 6667
    dir_ready = 'ready'
    dir_new_lists = 'new_lists'
    dir_old_lists = 'old_lists'
    log_file_name = 'log.log'
    max_concurrent_uploads = 16
    target_main = 'target'

    running = True
    logger = None
    irc_bot = None
    grab = None
    grab_running = True
    upload = None
    upload_running = True
