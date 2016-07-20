import settings
import os

def create_dir(name):
    if not os.path.isdir(name):
        os.makedirs(name)
        settings.logger.log("Created directory '{name}'".format(name=name))
