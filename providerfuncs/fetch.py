import os
import shutil
import time
import ctypes
from utils import log

LOG = log.get_module_log(__name__)

def get_free_space(path, logger=LOG):
    """
    helper function for examining free space on a drive
    :param path: directory that should be examined
    :param logger: instance of logging
    :return: - free_space_abs: absolute amount of free space in bytes
             - free_space_rel: percentage of available free space
    """

    # check if windows or unix
    if os.name == "nt":
        free_bytes, total_bytes = ctypes.c_ulonglong(0), ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, ctypes.pointer(total_bytes),
                                                   ctypes.pointer(free_bytes))
        free_space_abs = free_bytes.value
        free_space_rel = free_space_abs / total_bytes.value

    else:
        stat = os.statvfs(path)
        free_space_abs = stat.f_frsize * stat.f_bavail
        total_space = stat.f_frsize * stat.f_blocks
        free_space_rel = float(free_space_abs) / float(total_space)

    logger.info(
        time.ctime() + "\tFree space on hard drive: " + str(int(free_space_abs / 1024 / 1024)) + "MB which is " + \
        str(round(free_space_rel * 100, 2)) + "%")

    return free_space_abs, free_space_rel


def move_container(filename, target_dir, logger=LOG):
    """
    helper function for moving containers from network share to local drive
    --------------
    args:
        - filname: name of the file that will be moved
        - target_dir: directory on the local drive where the containers should be moved to (destination)
    """

    # move file
    shutil.move(filename, target_dir)

    # log containers that has been moved
    logger.info(time.ctime() + ":\tMoved container {} to {}".format(os.path.basename(filename), target_dir))

    # write LF to log for better readability
    logger.info("\n")

    return os.path.join(target_dir, os.path.basename(filename))


def handle_invalid_container(filename, rm_invalid=False, json_error=False, no_space=False, logger=LOG):
    """
    Will detect invalid containers and create a warning in log and if flag is set, also delete the correspnding
    containers.
    :param filename: name of the invalid file
    :param logger: instance of logging
    :param rm_invalid: remove invalid files if True
    :return:
    """

    source_dir = os.path.dirname(filename)

    if no_space:
        logger.info(time.ctime() + "\tnot enough space to fetch container {}".format(filename))
    elif json_error:
        logger.warning(time.ctime() + ":\t"
                                      "The container_config.json could not be read for this container:\n {}".format(filename))
    else:
        logger.warning(time.ctime() + ":\t"
                                      "The following container is provided by a person, who is not authorized to run "
                                      "containers on this machine:\n {}".format(filename))

    if rm_invalid:
        os.remove(filename)
    else:
        invalid_path = os.path.join(source_dir, 'invalid', '')
        if not os.path.exists(invalid_path):
            os.makedirs(invalid_path)
        if os.path.isfile(os.path.join(invalid_path, os.path.basename(filename))):
            os.remove(os.path.join(invalid_path, os.path.basename(filename)))
        shutil.move(filename, invalid_path)


def fetch(filename, target_dir, logger=LOG, rm_invalid=True):
    """
    move container from source to target dir
    :param filename: name of the file that will be moved
    :param target_dir: directory where files will be moved to
    :param logger: instance of logging
    :return: list of filenames that were moved
    """

    # check if enough space is present on hard drive
    free_space_abs, free_space_rel = get_free_space(target_dir)
    if free_space_abs < os.stat(filename).st_size:
        handle_invalid_container(filename, logger, rm_invalid, no_space=True)
        raise IOError(time.ctime() + "\tnot enough space to fetch container {}".format(filename))
    else:
        # move containers
        filename = move_container(filename, target_dir, logger)
        return filename

