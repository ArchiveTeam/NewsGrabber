import settings
import threading
import os
import random
import string


class Grab(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.grabs = {}

    def run(self):
        self.grab()

    def grab(self):
        while True:
            for list_ in os.listdir(settings.dir_new_lists):
                if not settings.grab_running:
                    continue
                random_string = ''.join(random.choice(string.ascii_lowercase) for num in range(10))
                new_name = list_+random_string
                os.rename(os.path.join(settings.dir_new_lists, list_),
                        os.path.join(settings.dir_old_lists, new_name))
                self.grabs[random_string] = threading.Thread(target=self.grab_single, args=(new_name,))
                self.grabs[random_string].daemon = True
                self.grabs[random_string].start()

    def grab_single(self, name):
        video_string = '--youtube-dl ' if '-videos' in name else ''
        extra_args = ' --1'
        os.system('~/.local/bin/grab-site --input-file {name} --level=0 --ua="ArchiveTeam; Googlebot/2.1" --no-sitemaps --concurrency=5{extra} --warc-max-size=524288000 --wpull-args="{video}--no-check-certificate --timeout=300" > /dev/null 2>&1'.format(
                name=os.path.join(settings.dir_old_lists, name),
                extra=extra_args, video=video_string))
