import docker, docker.errors
import os
import helper_process as hp
from providerfuncs import parse, fetch, build
from core.container import Container
import zipfile
from utils import log
import time
import traceback


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

    def sleep(self):
        time.sleep(self.fetcher_conf['sleep'])

    def provide(self):

        while 1:

            try:

                network_files = os.listdir(self.paths['network_containers'])

                # exclude failed dir if its inside the network dir
                if 'invalid' in network_files:
                    network_files.remove('invalid')

                for filename in network_files:

                    filename = os.path.join(self.paths['network_containers'], filename)

                    # get config from json
                    try:
                        container_config = parse.parse_zipped_config(filename)
                    except (RuntimeError, zipfile.BadZipfile) as e:
                        fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'], json_error=True)
                        self.logger.error(traceback.format_exc())
                        continue
                    if container_config is None:
                        fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'], json_error=True)
                        continue

                    # check for valid executor
                    if container_config.executor_name in self.fetcher_conf['executors']:
                        # move file to local drive
                        try:
                            filename = fetch.fetch(filename, self.paths['local_containers'])
                        except IOError:
                            self.logger.error(traceback.format_exc())
                            continue
                    else:
                        fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'])
                        continue

                    # generate docker image
                    try:
                        if container_config.build_flag:
                            image = build.build_image(filename, unzip_dir=self.paths['unzip'], tag=container_config.name)
                        else:
                            self.logger.error('\tloading tarred images is currently not implemented')
                            raise NotImplementedError
                            # image = build.load_image(filename)
                    except Exception:
                        self.logger.error(traceback.format_exc())
                        continue

                    # # create docker container
                    # try:
                    #     container = build.create_container(image, container_config, self.docker_conf['mounts'])
                    # except docker.errors.APIError as e:
                    #     continue

                    queue_container = Container(container_config, image, mounts=self.docker_conf['mounts'])
                    self.queue.put(queue_container)

                # leave the loop if terminate flag is set
                if self.term_flag.value:
                    break

                self.sleep()

            except Exception:
                self.logger.error(traceback.format_exc())
                self.stop()


    def start(self):
        super(Provider, self).start(self.provide, 'DoPQ-Provider')
        return self.process.pid

    def stop(self):
        self.term_flag.value = 1
        self.queue.close()
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



