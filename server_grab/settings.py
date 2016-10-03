import random

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

    version = 20161003.01
    irc_channel_bot = '#newsgrabberbot'
    irc_channel_main = '#newsgrabber'
    irc_nick = 'g_' + str(random.randint(0, 5000))
    irc_server_name = 'irc.underworld.no'
    irc_server_port = 6667
    dir_ready = 'warcs_ready'
    dir_new_lists = 'incoming_urls'
    dir_old_lists = 'incoming_urls_old'
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