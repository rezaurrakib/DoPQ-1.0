import docker, docker.errors
import os
import helper_process as hp
from providerfuncs import parse, fetch, build
from core import container as core_container
from time import sleep


class Provider(hp.HelperProcess):

    def __init__(self, config, queue):

        super(Provider, self).__init__()

        # get config settings
        self.paths = config['paths']
        self.fetcher_conf = config['fetcher']
        self.builder_conf = config['builder']
        self.docker_conf = config['docker']

        self.queue = queue

    def provide(self):

        network_dir = self.paths['network_dir']
        local_dir = self.paths['container_dir']
        unzip_dir = self.paths['unzip_dir']
        failed_dir = self.paths['failed_dir']
        remove_invalid = self.fetcher_conf['remove_invalid']
        mounts = self.docker_conf['mounts']
        queue = self.queue
        interval = self.fetcher_conf['sleep']

        while 1:

            network_files = os.listdir(network_dir)

            for filename in network_files:

                # get config from json
                try:
                    container_config = parse.parse_zipped_config(filename)
                except RuntimeError as e:
                    fetch.handle_invalid_container(filename, remove_invalid, json_error=True)
                    continue

                # check for valid executor
                if container_config.executor_name in self.fetcher_conf['executors']:
                    # move file to local drive
                    try:
                        filename = fetch.fetch(filename, local_dir)
                    except IOError as e:
                        continue
                else:
                    fetch.handle_invalid_container(filename, remove_invalid)
                    continue

                # generate docker image
                try:
                    if container_config.build_flag:
                        image = build.build_image(filename, unzip_dir, failed_dir, remove_invalid)
                    else:
                        image = build.load_image(filename, failed_dir, remove_invalid)
                except Exception as e:
                    continue

                # create docker container
                try:
                    container = build.create_container(image, container_config, mounts)
                except docker.errors.APIError as e:
                    continue

                queue_container = core_container.Container(container_config, container)
                queue.put(queue_container)

            sleep(interval)

    def start(self):
        super(Provider, self).start(self.provide())
        return self.process.pid



