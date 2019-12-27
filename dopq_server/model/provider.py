import os
import time
import zipfile
import datetime
import traceback
import multiprocessing as mp

from dopq_server.model.utils import log
from dopq_server.model.container_handler.container import Container
from dopq_server.model.docker_helper import docker_build, docker_fetch, docker_parser

LOG = log.get_module_log(__name__)

__authors__ = "Md Rezaur Rahman, Ilja Mankov, Markus Rohm"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"

class Provider():
    def __init__(self, config, queue):
        # get config settings
        self.provider_starttime = None
        self.container_queue = queue # Initially empty
        self.paths = config['paths']
        self.docker_conf = config['docker']
        self.fetcher_conf = config['fetcher']
        self.builder_conf = config['builder']
        self.logger = log.get_module_log(__name__)

    @property
    def status(self):
        if not isinstance(self.process, mp.Process):
            return 'not started'
        if self.process.exitcode is None:
            return 'running'
        else:
            return 'terminated'

    @property
    def uptime(self):
        days = 0
        elapsed_time = time.time() - self.provider_starttime
        elapsed_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        hours, minutes, seconds = map(int, elapsed_time.split(':'))
        #print("Hours: ", hours, " Minutes : ", minutes, " Seconds: ", seconds)
        if hours >= 24:
            days = hours / 24

        # convert information to print format
        uptime = ''
        uptime += '{}d '.format(days) if days else ''
        uptime += '{}h '.format(hours) if hours else ''
        uptime += '{}m '.format(minutes) if minutes else ''
        uptime += '{}s '.format(seconds) if seconds else ''

        return uptime, self.provider_startime_formatted

    def process_starttime(self):
        self.provider_starttime = time.time()
        self.provider_startime_formatted = datetime.datetime.fromtimestamp(self.provider_starttime).strftime("%A, %d.%b %H:%M:%S")

    def monitoring_provider(self):
        while True:
            try:
                network_files = os.listdir(self.paths['network_containers'])
                image = None
                dockerfile = None

                if 'invalid' in network_files:
                    network_files.remove('invalid')

                print("network_files: ", network_files)

                for filename in network_files:
                    zip_filename = filename
                    filename = os.path.join(self.paths['network_containers'], filename)
                    print("Printing filenames in network_files : ", filename)
                    container_config = self.check_container_config(filename)
                    # check for valid executor
                    if container_config.executor_name in self.fetcher_conf['executors']:
                        print("Contains a valid executor : ", container_config.executor_name)
                        filename = self.fetch_tolocal(filename)
                        print("Fetched the files in local directory")
                    else:
                        docker_fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'])

                    dockerfile = self.unzip_file(filename)

                    # Generate the docker image from the file
                    try:
                        if container_config.build_flag:
                            print("Building docker image from config file.")
                            image = self.build_file_as_dockerimage(filename, dockerfile, container_config.name)
                    except Exception:
                        self.logger.error(traceback.format_exc())

                    # Create docker container
                    print("Adding the docker image into the container queue ...")
                    new_container = self.build_docker_container(image, container_config)
                    # Adding new container in the container queue
                    self.container_queue.put(new_container)
                    print("Before sleep")
                self.provider_sleep()

            except Exception:
                self.logger.error(traceback.format_exc())
                print("Provider is about to stop ... ")
                self.provider_stop()


    def check_container_config(self, filename):
        """
         Checks for the container config file in zipped docker folder
        :param filename:
        :return: container_config obj
        """

        filename = os.path.join(self.paths['network_containers'], filename)
        container_config_file = None
        # check whether there is a container_config file present in the zipfile
        try:
            if zipfile.is_zipfile(filename):
                container_config_file = docker_parser.parse_zipped_config(filename)
            else:
                container_config_file = docker_parser.parse_unzipped_config(filename) # For unzipped folder checking
        except (RuntimeError, zipfile.BadZipfile):
            docker_fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'], json_error=True)
            self.logger.error(traceback.format_exc())
        if container_config_file is None:
            docker_fetch.handle_invalid_container(filename, self.fetcher_conf['remove_invalid'], json_error=True)

        return container_config_file

    def unzip_file(self, filename, unzip_dir=""):
        """
        unpack zipped container files
        :param filename: e.g., "/home/rrahman/Desktop/lmu_augen_repo/DOPQ_Config_Folders/container/folder_username.zip'
        :return: filename of the Dockerfile in the zipfile
        """
        # construct paths if not specified
        if not unzip_dir:
            unzip_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), 'unzip', "")
        try:
            dockerfile = docker_build.unzip_docker_files(filename, unzip_dir)
        except Exception as e:
            LOG.error('\terror while unzipping file {}:\n\t\t{}'.format(filename, e))
            raise e

        return dockerfile

    def fetch_tolocal(self, filename):
        """
        move file to the  local drive
        :param filename:
        :return: file
        """
        try:
            filename = docker_fetch.fetch(filename, self.paths['local_containers'])
        except IOError:
            self.logger.error(traceback.format_exc())

        return filename

    def build_file_as_dockerimage(self, filename, dockerfile_name, cont_config_tag):
        """
        generate docker image
        :param filename:
        :param dockerfile_name:
        :param cont_config_tag:
        :return: built docker image
        """
        image = None
        #print("DockerFile Name: ", dockerfile_name)
        image = docker_build.build_image(filename, dockerfile_name, unzip_dir=self.paths['unzip'], tag=cont_config_tag)
        return image

    def build_docker_container(self, image, container_config):
        queue_container = Container(container_config, image.id, mounts=self.docker_conf['mounts'])
        return queue_container

    def start_provider(self):
        """
        Start the provider process
        :return: Specific process id
        """
        print("Logged into the start provider")
        self.process_starttime()
        self.process = mp.Process(target=self.monitoring_provider, name='DoPQ-Provider')
        self.process.start()
        return self.process.pid

    def provider_sleep(self):
        """
        Wait before provider monitoring. Refer to. {File: config.ini, [fetcher] sleep.interval XX(ms)} to change
        :return: None
        """
        time.sleep(self.fetcher_conf['sleep'])

    def provider_stop(self):
        print("Provider is terminating")
        self.process.terminate()
        self.process.join()

