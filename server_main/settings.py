def init():
    global version
    global logger
    global irc_bot
    global irc_channel_bot
    global irc_channel_main
    global irc_nick
    global irc_server_name
    global irc_server_port
    global dir_new_urllists
    global dir_old_urllists
    global dir_donefiles
    global dir_ready
    global log_file_name
    global run_services
    global targets
    global targets_grab
    global targets_discovery
    global services
    global get_urls
    global get_urls_running
    global running
    global upload
    global upload_running
    global max_concurrent_uploads
    global dir_last_upload
    global max_item_size
    global max_url_age
    global dir_dumped_url_data
    global keys

    # variables to be changed
    version = 20161107.01
    irc_channel_bot = '#newsgrabberbot'
    irc_channel_main = '#newsgrabber'
    irc_nick = 'newsbuddy'
    irc_server_name = 'irc.underworld.no'
    irc_server_port = 6667
    dir_new_urllists = 'incoming_urls'
    dir_old_urllists = 'incoming_urls_old'
    dir_donefiles = 'recovery_url_data'
    dir_ready = 'warcs_ready'
    dir_last_upload = 'warcs_items'
    dir_dumped_url_data = 'dumped_url_data'
    log_file_name = 'log.log'
    targets = 'targets.json'
    targets_grab = 'rsync_targets'
    targets_discovery = 'rsync_targets_discovery'
    keys = 'keys'
    max_url_age = 1209600 # 2 weeks
    max_concurrent_uploads = 16
    max_item_size = 10737418240 # 10 GB

    # variables to be changed by script
    services = {}
    irc_bot = None
    logger = None
    run_services = None
    get_urls = None
    get_urls_running = True
    upload = None
    upload_running = True
    running = True
