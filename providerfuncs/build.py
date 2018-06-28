import shutil
import zipfile
import os
import time
import docker.errors
import docker
from utils import log

LOG = log.get_module_log(__name__)


def unzip_docker_files(filename, target_dir):
    """
    unpack zipped container files
    :param filename: filename of the zipfile
    :param target_dir: directory where contexts will be extracted
    :return: filename of the Dockerfile in the zipfile
    """

    try:
        z = zipfile.ZipFile(filename)

        # find Dockerfile
        files = z.namelist()
        dockerfile = [s for s in files if 'Dockerfile' in s][0]

        # extract and close
        z.extractall(target_dir)
        z.close()

    except Exception as e:
        os.remove(filename)
        raise e

    else:
        os.remove(filename)
        return os.path.join(target_dir, dockerfile)


def build_image(filename, unzip_dir="", tag=None, logger=LOG):
    """
    build docker image form zipfile
    :param filename: name of the zipfile
    :param unzip_dir: directory where files are extracted to temporarily
    :param tag: string which identifies the docker container to be build.
    :param logger: instance of logging
    :return: docker image
    """

    if tag is None:
        tag = filename.lower()
        LOG.warning("Please explicitly provide a tag for the building process. If None is given the "
                    "lower case of filename will be used, which is deprecated!")

    # construct paths if none are passed
    if not unzip_dir:
        unzip_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), 'unzipped', "")

    # unzip files
    try:
        dockerfile = unzip_docker_files(filename, unzip_dir)
    except Exception as e:
        logger.error(time.ctime() + '\terror while unzipping file {}:\n\t\t{}'.format(filename, e))
        raise e

    # build docker image after successful unzip
    else:
        filename = "".join(os.path.basename(filename).split('.')[:-1])
        try:
            client = docker.from_env()
            image = client.images.build(path=os.path.dirname(dockerfile), rm=True, tag=tag)
        except (docker.errors.BuildError, docker.errors.APIError) as e:
            logger.error(time.ctime() + '\terror while building image {} (tag={}):\n\t\t{}'.format(filename, tag, e))
            clear_unzipped(unzip_dir, filename)
            raise e
        else:
            logger.info(time.ctime() + '\tsuccessfully build image {} (tag={})'.format(filename, tag))
            clear_unzipped(unzip_dir)
            return image


def load_image(filename, failed_dir="", rm_invalid=False, logger=LOG):
    """
    load docker image form tar file
    :param filename: name of the tar file
    :param logger: instance of logging
    :param failed_dir: directory where files are moved when build fails (if rm_invalid=True)
    :param rm_invalid: indicates whether failed builds are removed or moved
    :return: docker image
    """

    # construct paths if none are passed
    if not failed_dir:
        failed_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), 'failed', "")

    with open(filename, 'r') as f:
        data = f.read()
    try:
        client = docker.from_env()
        output = client.images.load(data).next()

        if 'error' in output.keys():
            clear_unzipped(filename, failed_dir, rm_invalid)
            raise Exception('error while loading image: ' + output['errorDetails'])

        else:
            os.remove(filename)
            image = client.images.get(output['stream'][len('Loaded image: '):-1])
            logger.info(time.ctime() + '\tsuccessfully loaded image {}'.format(filename))
            return image  # image.attrs['RepoTags'][0]

    except Exception as e:
        logger.error(time.ctime() + '\t{}'.format(e))
        clear_unzipped(filename, failed_dir, rm_invalid)
        raise e


def clear_unzipped(unzip_dir, filename=None, logger=LOG):
    """
    helper for handling files which could not be built
    :param unzip_dir: directory where the files have been unzipped to
    :param filename: name of the failed file
    :param logger: instance of logging or colorlog
    :return: None
    """
    # log a fail message
    if filename is None:
        logger.warn(time.ctime() + '\t{} could not be build'.format(filename))

    if os.path.isdir(unzip_dir):
        # remove unzipped files
        contents = os.listdir(unzip_dir)
        for item in contents:
            item = os.path.join(unzip_dir, item)
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)


def create_mounts(mount_list, user):
    """
    converts string to docker.type.Mount objects, also automatically adds user folder to /outdir
    :param mount_list: list of docker mount strings (as given in the config.ini)
    :param user: user for whom the mounts are created
    :return: list of docker.types.Mount objects, same len as mount_list
    """

    if mount_list == ['']:
        return None

    mounts = []
    for mount in mount_list:

        # split mount string in source and target
        mount = mount.split(':')

        # append user folder to source if target is outdir
        if mount[1] == '/outdir':
            mount[0] = os.path.join(mount[0], user)
        if not os.path.exists(mount[0]):
            os.makedirs(mount[0])

        # create Mount object and append to list
        mount = docker.types.Mount(source=mount[0], target=mount[1], type='bind')
        mounts.append(mount)

    return mounts


def create_container(image, config, mounts, logger=LOG):
    """
    create a docker container using a passed ContainerConfig object
    :param image: docker image on which the container will be based
    :param config: ContainerConfig object
    :param mounts: list of mount pairs (/dir:/dir)
    :param logger: instance of logging or colorlog
    :return: docker container
    """

    mounts = create_mounts(mounts, config.executor_name)
    client = docker.from_env()
    try:
        create_conf = config.docker_params(image=image, detach=True, mounts=mounts)
        container = client.containers.create(**create_conf)
    except docker.errors.APIError as e:
        logger.error(e)
        raise e

    return container

