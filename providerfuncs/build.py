import shutil
import zipfile
import os
import time
import docker.errors
import docker


def unzip_docker_files(source_dir, target_dir, image_name):

    try:
        filename = os.path.join(source_dir, image_name)
        z = zipfile.ZipFile(filename)
        folder_name = "".join(image_name.split('.')[0:-1])
        # TODO add functionality to check wheter zipped file contains folder, create one if not
        z.extractall(target_dir)
        z.close()

    except Exception as e:
        raise e

    else:
        os.remove(filename)
        return os.path.join(target_dir, folder_name, "")


def build_image(source_dir, image_name, logger, unzip_dir="", load_dir="", failed_dir="", rm_invalid=False):

    #construct paths if none are passed
    if not unzip_dir:
        unzip_dir = os.path.join(os.path.dirname(os.path.abspath(source_dir)), 'unzipped', "")
    if not load_dir:
        load_dir = os.path.join(os.path.dirname(os.path.abspath(source_dir)), 'loaded', "")
    if not failed_dir:
        failed_dir = os.path.join(os.path.dirname(os.path.abspath(source_dir)), 'failed', "")

    # unzip files
    try:
        foldername = unzip_docker_files(source_dir, unzip_dir, image_name)
    except Exception as e:
        logger.error(time.ctime() + '\terror while unzipping file {}:\n\t\t{}'.format(image_name, e))
        handle_failed_files(source_dir, image_name, failed_dir,  rm_invalid)
        raise e

    # build docker image after successful unzip
    else:
        image_name = "".join(image_name.split('.')[:-1])
        try:
            client = docker.from_env()
            image = client.images.build(path=foldername, rm=True, tag=image_name.lower())
        except (docker.errors.BuildError, docker.errors.APIError) as e:
            logger.error(time.ctime() + '\terror while building image {}:\n\t\t{}'.format(image_name, e))
            handle_failed_files(source_dir, image_name, failed_dir, rm_invalid)
            raise e
        else:
            logger.info(time.ctime() + '\tsuccessfully build image {}'.format(image_name))
            handle_failed_files(source_dir, image_name, failed_dir)
            return image


def load_image(source_dir, image_name, logger, failed_dir="", rm_invalid=False):

    # construct paths if none are passed
    if not failed_dir:
        failed_dir = os.path.join(os.path.dirname(os.path.abspath(source_dir)), 'failed', "")

    filename = os.path.join(source_dir, image_name)
    with open(filename, 'r') as f:
        data = f.read()
    try:
        client = docker.from_env()
        output = client.images.load(data).next()

        if 'error' in output.keys():
            handle_failed_files(source_dir, image_name, failed_dir, rm_invalid)
            raise Exception('error while loading image: ' + output['errorDetails'])

        else:
            os.remove(filename)
            image = client.images.get(output['stream'][len('Loaded image: '):-1])
            logger.info(time.ctime() + '\tsuccessfully loaded image {}'.format(image_name))
            return image  # image.attrs['RepoTags'][0]

    except Exception as e:
        logger.error(time.ctime() + '\t' + e)
        raise e


def handle_failed_files(path, filename, failed_dir, rm=True):

    path = os.path.join(path, filename)

    # remove file if rm flag is set, move otherwise
    if rm:
        shutil.rmtree(path)
    else:
        dest = os.path.join(failed_dir, filename)
        if os.path.exists(dest): shutil.rmtree(dest)
        shutil.move(path, dest)


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


def create_container(image, config, mounts, gpu_minors):

    mounts = create_mounts(mounts, config.executor)
    client = docker.from_env()
    create_conf = config.docker_params(image=image, detach=True, mounts=mounts,
                                       environment=["NVIDIA_VISIBLE_DEVICES=" + str(gpu_minors)])
    container = client.containers.create(**create_conf)

    return container

