import threading
import os
import random
import string
import time
import file

import settings


class Grab(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.grabs = {}

    def run(self):
        self.grab()

    def grab(self):
        while True:
            for filename in os.listdir(settings.dir_new_lists):
                if not settings.grab_running:
                    continue
                print filename
                filename_urls = os.path.join(settings.dir_old_lists, filename + '_urls')
                filejson = file.File(os.path.join(settings.dir_new_lists, filename)).read_json()
                if filejson['nick'] != settings.irc_nick:
                    settings.irc_bot.set_nick(filejson['nick'])
                file.File(filename_urls).write_lines(filejson['urls'])
                os.rename(os.path.join(settings.dir_new_lists, filename),
                        os.path.join(settings.dir_old_lists, filename))
                self.grabs[filename] = threading.Thread(target=self.grab_single, args=(filename_urls,))
                self.grabs[filename].daemon = True
                self.grabs[filename].start()
            time.sleep(10)

    @staticmethod
    def grab_single(name):
        video_string = '--youtube-dl ' if '-videos' in name else ''
        extra_args = ' --1'
        os.system('~/.local/bin/grab-site --input-file {name} --level=0 --ua="ArchiveTeam; Googlebot/2.1" --no-sitemaps --concurrency=5{extra} --warc-max-size=524288000 --wpull-args="{video}--no-check-certificate --timeout=300" > /dev/null 2>&1'.format(
            name=name, extra=extra_args, video=video_string))
        os.remove(name)
