import docker
import os
import shutil
import helper_process as hp
import zipfile


class Provider(hp.HelperProcess):

    def __init__(self, config):

        super(Provider, self).__init__()

        # get config settings
        self.paths = config['paths']
        self.fetcher_conf = config['fetcher']
        self.builder_conf = config['builder']
        self.docker_conf = config['docker']

    def single_run(self):
        pass

    def get_jsons(self):
        pass

    def provide(self):

        while 1:
            # get jsons
            # weed out invalid containers

            # fetch valid containers

            #
            pass