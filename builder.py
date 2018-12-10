import docker
import shutil
import zipfile
import os
import logging
import time
import docker.errors
import multiprocessing as mp
import helper_process as hp


class Builder(hp.HelperProcess):

    def __init__(self, config, queue):

        super(Builder, self).__init__()

        # make sure queue is mp.Queue
        assert (type(queue) is mp.queues.Queue)

        # init members
        self.paths = config['paths']
        self.config = config['builder']
        self.queue = queue
        self.client = docker.from_env()
        self.build_list = []

        # init logging
        self.logger = logging.getLogger('builder')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler(os.path.join(self.paths['log'], 'builder.log')))
        self.logger.info(time.ctime() + '\tinitializing builder')

    def unzip_docker_files(self, image_name):

        try:
            filename = os.path.join(self.paths['local_containers'], image_name)
            z = zipfile.ZipFile(filename)
            folder_name = "".join(image_name.split('.')[0:-1])
            z.extractall(self.paths['unzip'])
            z.close()

        except Exception as e:
            raise e

        else:
            os.remove(filename)
            return os.path.join(self.paths['unzip'], folder_name, "")

    def build_image(self, image_name):

        try:
            foldername = self.unzip_docker_files(image_name)
        except Exception as e:
            self.logger.error(time.ctime() + '\terror while unzipping file {}: '
                                             '\n\t\t{}'.format(image_name, e))
            self.handle_failed_files(self.paths['local_containers'], image_name, self.config['remove_invalid'])
            raise e

        else:
            image_name = "".join(image_name.split('.')[:-1])
            try:
                image = self.client.images.build(path=foldername, rm=True, tag=image_name.lower())
            except (docker.errors.BuildError, docker.errors.APIError) as e:
                self.logger.error(time.ctime() + '\terror while building image {}: '
                                                 '\n\t\t{}'.format(image_name, e))
                self.handle_failed_files(self.paths['unzip'], image_name, self.config['remove_invalid'])
                raise e
            else:
                self.logger.info(time.ctime() + '\tsuccessfully build image {}'.format(image_name))
                self.handle_failed_files(self.paths['unzip'], image_name)
                return image.attrs['RepoTags'][0]

    def load_image(self, image_name):

        filename = os.path.join(self.paths['local_containers'], image_name)
        with open(filename, 'r') as f:
            data = f.read()
        try:
            output = self.client.images.load(data)
            output = next(output)

            if 'error' in list(output.keys()):
                self.handle_failed_files(self.paths['local_containers'], image_name, self.config['remove_invalid'])
                raise Exception('error while loading image: ' + output['errorDetails'])

            else:
                os.remove(filename)
                image = self.client.images.get(output['stream'][len('Loaded image: '):-1])
                self.logger.info(time.ctime() + '\tsuccessfully loaded image {}'.format(image_name))
                return image.attrs['RepoTags'][0]

        except Exception as e:
            self.logger.error(time.ctime() + '\t' + e)
            raise e

    def handle_failed_files(self, path, filename, rm=True):

        path = os.path.join(path, filename)

        # remove file if rm flag is set, move otherwise
        if rm:
            shutil.rmtree(path)
        else:
            dest = os.path.join(self.paths['failed'], filename)
            if os.path.exists(dest): shutil.rmtree(dest)
            shutil.move(path, dest)

    def build(self):

        while 1:
            # get files in the source directory
            self.build_list = os.listdir(self.paths['local_containers'])

            # build the files
            for filename in self.build_list:

                # get suffix of the file
                suffix = filename.split('.')[-1]

                # build file according to suffix
                # noinspection PyBroadException
                try:
                    image = None
                    if suffix in self.config['build']:
                        image = self.build_image(filename)
                    elif suffix in self.config['load']:
                        image = self.load_image(filename)
                    else:
                        self.logger.error(time.ctime() + '\tcould not build/load file {}:'
                                                         ' file extension unknown'.format(filename))
                        self.handle_failed_files(self.paths['local_containers'], filename)
                except Exception:
                    continue
                else:
                    self.queue.put(image)

            # wait specified time
            time.sleep(self.config['sleep'])

        pass

    def start(self):

        super(Builder, self).start(self.build)
        return self.process.pid
