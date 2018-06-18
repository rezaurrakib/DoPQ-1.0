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

        network_dir = self.paths['network_dir']
        local_dir = self.paths['container_dir']
        unzip_dir = self.paths['unzip_dir']
        load_dir = self.paths['load_dir']
        failed_dir = self.paths['failed_dir']

        while 1:

            network_files = os.path.walk(network_dir)

            for filename in network_files:

                container_config =
            # get json
            # weed out invalid container

            # fetch valid container

            # generate image

            # generate container

            # build container object
            pass