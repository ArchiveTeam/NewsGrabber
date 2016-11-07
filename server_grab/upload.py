import threading
import os
import shutil
import time

import file
import settings


class Upload(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.concurrent_uploads = 0
        self.max_concurrent_uploads = settings.max_concurrent_uploads
        self.target = file.File(settings.target_main)
        self.uploads = {}

    def run(self):
        self.move_warcs()

    def move_warcs(self):
        while True:
            for dir_ in [dir_ for dir_ in os.listdir('.') if os.path.isdir(dir_)]:
                if dir_ == settings.dir_ready:
                    continue
                while not settings.upload_running:
                    time.sleep(1)
                files = [file for file in os.listdir(dir_) if os.path.isfile(os.path.join(dir_, file)) and file.endswith('.warc.gz')]
                grab_finished = len(filter(lambda file: file.endswith('-meta.warc.gz'), files)) != 0
                if grab_finished:
                    for file in files:
                        os.rename(os.path.join(dir_, file), os.path.join(settings.dir_ready, file))
                else:
                    for file in files:
                        warc_num = int(file[-13:-8])
                        warc_num_second = str(warc_num + 1).zfill(5)
                        if file[:-13] + warc_num_second + '.warc.gz' in file:
                            os.rename(os.path.join(dir_, file), os.path.join(settings.dir_ready, file))
                if grab_finished:
                    shutil.rmtree(dir_)
            self.upload()
            time.sleep(10)

    def set_max_concurrent_uploads(self, change):
        if self.max_concurrent_uploads + change > settings.max_concurrent_uploads:
            self.max_concurrent_uploads = settings.max_concurrent_uploads
            return
        if self.max_concurrent_uploads + change < 1:
            return
        self.max_concurrent_uploads += change

    def upload(self):
        for file in [file for file in os.listdir(settings.dir_ready) if file.endswith('.warc.gz')
                and not os.path.isfile(os.path.join(settings.dir_ready, file+'.upload'))]:
            while not settings.upload_running:
                time.sleep(1)
            time.sleep(1)
            while self.concurrent_uploads > self.max_concurrent_uploads:
                time.sleep(1)
            self.uploads[file] = threading.Thread(target=self.upload_single, args=(file,))
            self.uploads[file].daemon = True
            self.uploads[file].start()

    def upload_single(self, file):
        self.concurrent_uploads += 1
        open(os.path.join(settings.dir_ready, file+'.upload'), 'a').close()
        os.system('rsync -avz --no-o --no-g --progress --remove-source-files {file} {target}'.format(
            file=os.path.join(settings.dir_ready, file), target=self.target.read()))
        self.concurrent_uploads -= 1
        os.remove(os.path.join(settings.dir_ready, file+'.upload'))
        if os.path.isfile(os.path.join(settings.dir_ready, file)):
            settings.irc_bot.send('PRIVMSG', '{name} synced unsuccessful to main server.'.format(
                name=file), settings.irc_channel_bot)
            self.set_max_concurrent_uploads(-1)
        else:
            self.set_max_concurrent_uploads(1)