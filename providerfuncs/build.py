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
    :return: foldername (with dir) that contains the extracted files
    """

    try:
        z = zipfile.ZipFile(filename)
        folder_name = "".join(filename.split('/')[-1].split('.')[0:-1])
        # TODO add functionality to check whether zipped file contains folder, create one if not
        z.extractall(target_dir)
        z.close()

    except Exception as e:
        raise e

    else:
        os.remove(filename)
        return os.path.join(target_dir, folder_name, "")


def build_image(filename, unzip_dir="", failed_dir="", rm_invalid=False, logger=LOG):
    """
    build docker image form zipfile
    :param filename: name of the zipfile
    :param logger: instance of logging
    :param unzip_dir: directory where files are extracted to temporarily
    :param failed_dir: directory where files are moved when build fails (if rm_invalid=True)
    :param rm_invalid: indicates whether failed builds are removed or moved
    :return: docker image
    """

    # construct paths if none are passed
    if not unzip_dir:
        unzip_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), 'unzipped', "")
    if not failed_dir:
        failed_dir = os.path.join(os.path.dirname(os.path.dirname(filename)), 'failed', "")

    # unzip files
    try:
        unzipped_folder = unzip_docker_files(filename, unzip_dir)
    except Exception as e:
        logger.error(time.ctime() + '\terror while unzipping file {}:\n\t\t{}'.format(filename, e))
        handle_failed_file(filename, failed_dir, rm_invalid)
        raise e

    # build docker image after successful unzip
    else:
        filename = "".join(filename.split('.')[:-1])
        try:
            client = docker.from_env()
            image = client.images.build(path=unzipped_folder, rm=True, tag=filename.lower())
        except (docker.errors.BuildError, docker.errors.APIError) as e:
            logger.error(time.ctime() + '\terror while building image {}:\n\t\t{}'.format(filename, e))
            handle_failed_file(filename, failed_dir, rm_invalid)
            raise e
        else:
            logger.info(time.ctime() + '\tsuccessfully build image {}'.format(filename))
            handle_failed_file(filename, failed_dir)
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
            handle_failed_file(filename, failed_dir, rm_invalid)
            raise Exception('error while loading image: ' + output['errorDetails'])

        else:
            os.remove(filename)
            image = client.images.get(output['stream'][len('Loaded image: '):-1])
            logger.info(time.ctime() + '\tsuccessfully loaded image {}'.format(filename))
            return image  # image.attrs['RepoTags'][0]

    except Exception as e:
        logger.error(time.ctime() + '\t' + e)
        handle_failed_file(filename, failed_dir, rm_invalid)
        raise e


def handle_failed_file(filename, failed_dir, rm=True):
    """
    helper for handling files which could not be built
    :param filename: name of the failed file
    :param failed_dir: directory where files are moved when build fails (if rm_invalid=True)
    :param rm: indicates whether failed builds are removed or moved
    :return: None
    """

    # remove file if rm flag is set, move otherwise
    if rm:
        shutil.rmtree(filename)
    else:
        dest = os.path.join(failed_dir, filename)
        if os.path.exists(dest): shutil.rmtree(dest)
        shutil.move(filename, dest)


def create_mounts(mount_list, user):
    """
    converts string to docker.type.Mount objects, also automatically adds user folder to /outdir
    :param mount_list: list of docker mount strings (as given in the config.ini)
    :param user: user for whom the mounts are created
    :return: list of docker.types.Mount objects, same len as mount_list
    """

    if mount_list == ['']: return None

    mounts = []
    for mount in mount_list:

        # split mount string in source and target
        mount = mount.split(':')

        # append user folder to source if target is outdir
        if mount[1] == '/outdir': mount[0] = os.path.join(mount[0], user)
        if not os.path.exists(mount[0]): os.makedirs(mount[0])

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
    :return: docker container
    """

    mounts = create_mounts(mounts, config.executor)
    client = docker.from_env()
    try:
        create_conf = config.docker_params(image=image, detach=True, mounts=mounts)
        container = client.containers.create(**create_conf)
    except docker.errors.APIError as e:
        logger.error(e)
        raise e

    return container

