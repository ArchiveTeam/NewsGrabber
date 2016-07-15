def init():
    global version
    global logger
    global access_key
    global secret_key
    global irc_bot
    global irc_channel_bot
    global irc_channel_main
    global irc_nick
    global irc_server_name
    global irc_server_port
    global dir_new_urllists
    global dir_old_urllists
    global dir_donefiles
    global log_file_name
    global run_services
    global targets_grab
    global targets_discovery
    global services

    # variables to be changed
    version = 20160715.01
    irc_channel_bot = '#newsgbot'
    irc_channel_main = '#newsg'
    irc_nick = 'newsbud4'
    irc_server_name = 'irc.underworld.no'
    irc_server_port = 6667
    access_key = 'access_key'
    secret_key = 'secret_key'
    dir_new_urllists = 'new_urllists'
    dir_old_urllists = 'old_urllists'
    dir_donefiles = 'donefiles'
    log_file_name = 'log.log'
    targets_grab = 'rsync_targets'
    targets_discovery = 'rsync_targets_discovery'

    # variables to be changed by script
    services = {}
    irc_bot = None
    logger = None
    run_services = None
    get_urls = None
