import docker, docker.errors
import os
import helper_process as hp
from providerfuncs import parse, fetch, build
from core.container import Container
from time import sleep
import zipfile
from utils import log
from time import ctime


class Provider(hp.HelperProcess):

    def __init__(self, config, queue):

        super(Provider, self).__init__()

        # get config settings
        self.paths = config['paths']
        self.fetcher_conf = config['fetcher']
        self.builder_conf = config['builder']
        self.docker_conf = config['docker']

        self.queue = queue
        self.logger = log.get_module_log(__name__)

    def provide(self):

        network_dir = self.paths['network_containers']
        local_dir = self.paths['local_containers']
        unzip_dir = self.paths['unzip']
        remove_invalid = self.fetcher_conf['remove_invalid']
        mounts = self.docker_conf['mounts']
        queue = self.queue
        interval = self.fetcher_conf['sleep']

        while 1:

            network_files = os.listdir(network_dir)

            # exclude failed dir if its inside the network dir
            if 'invalid' in network_files:
                network_files.remove('invalid')

            for filename in network_files:

                filename = os.path.join(network_dir, filename)

                # get config from json
                try:
                    container_config = parse.parse_zipped_config(filename)
                except (RuntimeError, zipfile.BadZipfile) as e:
                    fetch.handle_invalid_container(filename, remove_invalid, json_error=True)
                    continue
                if container_config is None:
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
                        image = build.build_image(filename, unzip_dir)
                    else:
                        self.logger.error(ctime() + '\tloading tarred images is currently not implemented')
                        raise NotImplementedError
                        #image = build.load_image(filename)
                except Exception as e:
                    continue

                # create docker container
                try:
                    container = build.create_container(image, container_config, mounts)
                except docker.errors.APIError as e:
                    continue

                queue_container = Container(container_config, container)
                queue.put(queue_container)

                # leave the loop if terminate flag is set
                if self.term_flag.value:
                    exit(0)

            sleep(interval)

    def start(self):
        super(Provider, self).start(self.provide)
        return self.process.pid

    def stop(self):
        self.term_flag.value = 1
        if self.status == 'running':
            self.process.join(timeout=None)


def test_provider():
    from pathos.helpers import mp
    import shutil

    test_config = {
        'paths': {'local_containers': 'test/dest/',
                  'network_containers': 'test/src/',
                  'unzip': 'test/unzipped/',
                  'log': 'test/log/',
                  'history': './',
                  'failed': 'test/failed/'},
        'docker': {'mounts': ['/home/kazuki/:/blub'],
                   'auto_remove': False,
                   'mem_limit': '32gb',
                   'network_mode': 'host',
                   'logging_interval': 30},
        'builder': {'sleep': 10,
                    'load': '.tar',
                    'build': '.zip'},
        'fetcher': {'remove_invalid': False,
                    'sleep': 10,
                    'min_space': 0.01,
                    'executors': 'ilja'}}

    backup_dir = 'test/backup'
    testfiles = os.listdir(backup_dir)
    testfiles = [tf for tf in testfiles if '.zip' in tf]
    print(testfiles)

    for testfile in testfiles:
        testfile = os.path.join(backup_dir, testfile)
        shutil.copy(testfile, test_config['paths']['network_containers'])

    q = mp.Queue()
    p = Provider(test_config, q)
    p.start()
    while p.status == 'running':
        try:
            image = q.get()
            print(image)
        except BaseException:
            p.stop()



if __name__ == '__main__':
    test_provider()



