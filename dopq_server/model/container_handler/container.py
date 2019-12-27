# !/usr/bin/env python
# encoding: utf-8
"""
container.py

Provides a wrapper for container objects
"""

# from docker.models.containers import Container as DockerContainer
# from core.containerconfig import ContainerConfig

import os
import time
import docker
import traceback

from dateutil import parser
from datetime import datetime
from docker.errors import APIError
from dopq_server.model.utils import log
from dopq_server.model.utils.cpu import CPU
from dopq_server.model.utils.gpu import get_gpus_status, get_gpu_infos
from dopq_server.model.container_handler.container_config import ContainerConfig


LOG = log.get_module_log(__name__)


class Container:
    """
    Wrapper for docker container objects
    """

    def __init__(self, config, image_id, log_dir=None, mounts=None):
        """
        Creates a new container instance.

        :param config: Provides a run configuration for the docker container.
        :param container_obj: The underlying docker container instance.
        """

        self.config = config
        self.container_id = None
        self.image_id = image_id
        self.last_log_update = int(time.time())
        self.last_log_file_update = int(time.time())
        self.log_dir = log_dir if log_dir is not None else ""
        self._stats = None
        self._gpu_minors = None
        self.created_at = datetime.fromtimestamp(time.time()).strftime("%a, %d.%b %H:%M")
        try:
            iter(mounts)
        except TypeError:
            self.mounts = ['']
        else:
            self.mounts = mounts
        self.mounts = self.create_mounts()

    @property
    def container_obj(self):
        if self.container_id is None:
            return None
        client = docker.from_env()
        return client.containers.get(self.container_id)

    @property
    def image(self):
        client = docker.from_env()
        return client.images.get(self.image_id)

    @property
    def start_time(self):
        """
        wrapper for getting the creation time of the container object
        :return: creation date and time as unicode
        """
        self.reload()
        state_val = self.container_obj.attrs.get('State')
        if state_val is not None:
            start_val = state_val.get('StartedAt')
            if start_val is not None:
                return parser.parse(start_val).replace(tzinfo=None)

        # fall back
        return datetime.utcnow()

    @property
    def finish_time(self):
        """
        wrapper for getting the creation time of the container object
        :return: creation date and time as unicode
        """

        self.reload()
        state_val = self.container_obj.attrs.get('State')
        if state_val is not None:
            start_val = state_val.get('FinishedAt')
            if start_val is not None:
                finish_time = parser.parse(start_val).replace(tzinfo=None)
                if finish_time == datetime(2001, 1, 1, 0, 0) and self.status != 'created':
                    # container is still running
                    return datetime.utcnow()
                else:
                    return finish_time

        # fall back
        return datetime.utcnow().replace(day=1, month=1, year=1, hour=0, minute=0, second=0, microsecond=0)

    @property
    def use_gpu(self):
        """
        helper for seeing if the container requires gpu
        :return True if use of gpus is specified in the ContainerConfig object
        """
        return bool(self.config.num_gpus)

    @property
    def user(self):
        """
        wrapper for accessing the username from the config
        :return: name of the executing user
        """
        return self.config.executor_name

    @property
    def run_time(self):
        """
        Returns the runtime string.
        :return: Run time as {hours}h {minutes}m {seconds}s
        """

        # try to get finish time, replace with now if not yet finished.
        end_time = self.finish_time
        if end_time.year == 1:
            end_time = datetime.utcnow()

        # calc delta
        time_delta = end_time - self.start_time
        time_delta = int(time_delta.total_seconds())

        minutes, seconds = divmod(time_delta, 60)
        hours, minutes = divmod(minutes, 60)

        runtime = ''
        runtime += '{}h '.format(hours) if hours > 0 else ''
        runtime += '{}m '.format(minutes) if minutes > 0 else ''
        runtime += '{}s '.format(seconds) if minutes == 0 else ''

        return runtime

    @property
    def name(self):
        """
        Provides the real name for the container (the one which is provided by user through config)
        :return: Name of the container
        """
        return self.config.name

    @property
    def executor(self):
        """
        Returns the person who started the container.
        :return: Name of the person who started the container.
        """
        return self.config.executor_name

    @property
    def docker_name(self):
        """
        Provides the name of the container given by docker
        :return: Name of the container given by docker
        """
        return self.container_obj.name

    @property
    def status(self):
        """
        The status of the container. For example, ``running``, or ``exited``.
        """
        if self.container_id is None:
            return 'not created'
        else:
            self.reload()
            return self.container_obj.status

    def attach(self, **kwargs):
        """
        Attach to this container.

        :py:meth:`logs` is a wrapper around this method, which you can
        use instead if you want to fetch/stream container output without first
        retrieving the entire backlog.

        Args:
            stdout (bool): Include stdout.
            stderr (bool): Include stderr.
            stream (bool): Return container output progressively as an iterator
                of strings, rather than a single string.
            logs (bool): Include the container's previous output.

        Returns:
            By default, the container's output as a single string.

            If ``stream=True``, an iterator of output strings.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.attach(**kwargs)

    def exec_run(self, cmd, stdout=True, stderr=True, stdin=False, tty=False,
                 privileged=False, user='', detach=False, stream=False,
                 socket=False, environment=None):
        """
        Run a command inside this container. Similar to
        ``docker exec``.

        Args:
            cmd (str or list): Command to be executed
            stdout (bool): Attach to stdout. Default: ``True``
            stderr (bool): Attach to stderr. Default: ``True``
            stdin (bool): Attach to stdin. Default: ``False``
            tty (bool): Allocate a pseudo-TTY. Default: False
            privileged (bool): Run as privileged.
            user (str): User to execute command as. Default: root
            detach (bool): If true, detach from the exec command.
                Default: False
            stream (bool): Stream response data. Default: False
            socket (bool): Return the connection socket to allow custom
                read/write operations. Default: False
            environment (dict or list): A dictionary or a list of strings in
                the following format ``["PASSWORD=xxx"]`` or
                ``{"PASSWORD": "xxx"}``.

        Returns:
            (generator or str):
                If ``stream=True``, a generator yielding response chunks.
                If ``socket=True``, a socket object for the connection.
                A string containing response data otherwise.
        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.exec_run(cmd, stdout, stderr, stdin, tty, privileged, user, detach, stream,
                                           socket, environment)

    def start(self, **kwargs):
        """
        Start this container. Similar to the ``docker start`` command, but
        doesn't support attach options.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """

        # check status
        if self.status == 'running' or self.status == 'restarting':
            LOG.warning("Container is already running or restarting (status={}). "
                        "Calling start has no effect here!".format(self.status))
            return self

        # for non-paused containers
        if self.status != 'paused':

            # read number of requested GPUs from config
            n_gpus = self.config.num_gpus

            # gpus required?
            if n_gpus > 0:

                # get free gpus
                free_gpus, _ = get_gpus_status()

                # set minors
                if len(free_gpus) < n_gpus:
                    # report problem
                    raise IOError("Not enough GPUs available to run container "
                                  "(available={}, required={})!".format(len(free_gpus), n_gpus))

                # assign
                minors = [str(m) for m in free_gpus[:n_gpus]]
                self.gpu_minors = minors

            else:
                self.gpu_minors = ['none']

            # create the container
            try:

                self.create_container()
            except APIError as e:
                LOG.error(traceback.format_exc())
                raise e

            # start it
            self._stats = self.container_obj.stats(decode=True, stream=True)
            return self.container_obj.start(**kwargs)

        else:

            LOG.warning("You should not call start to unpause a paused container!")
            self._stats = self.container_obj.stats(decode=True, stream=True)
            return self.container_obj.unpause(**kwargs)

    def restart(self, **kwargs):
        """
        Restart this container. Similar to the ``docker restart`` command.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.restart(**kwargs)

    def pause(self):
        """
        Pauses all processes within this container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.pause()

    def unpause(self):
        """
        Unpause all processes within the container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.unpause()

    def stop(self):
        """
        Stops a container. Similar to the ``docker stop`` command.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.stop()

    def kill(self, signal=None):
        """
        Kill or send a signal to the container.

        Args:
            signal (str or int): The signal to send. Defaults to ``SIGKILL``

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.kill(signal)

    def get_archive(self, path):
        """
        Retrieve a file or folder from the container in the form of a tar
        archive.

        Args:
            path (str): Path to the file or folder to retrieve

        Returns:
            (tuple): First element is a raw tar data stream. Second element is
            a dict containing ``stat`` information on the specified ``path``.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.get_archive(path)

    def put_archive(self, path, data):
        """
        Insert a file or folder in this container using a tar archive as
        source.

        Args:
            path (str): Path inside the container where the file(s) will be
                extracted. Must exist.
            data (bytes): tar data to be extracted

        Returns:
            (bool): True if the call succeeds.

        Raises:
            :py:class:`~docker.errors.APIError` If an error occurs.
        """
        return self.container_obj.put_archive(path, data)

    def remove(self, **kwargs):
        """
        Remove this container. Similar to the ``docker rm`` command.

        Args:
            v (bool): Remove the volumes associated with the container
            link (bool): Remove the specified link and not the underlying
                container
            force (bool): Force the removal of a running container (uses
                ``SIGKILL``)

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.remove(**kwargs)

    def reload(self):
        try:
            self.container_obj.reload()
        except Exception:
            pass

    @property
    def stats(self):
        """
        wrapper that return the next item of the stats stream that is created in init
        """
        if self._stats is None or not iter(self._stats) is iter(self._stats):
            self._stats = self.container_obj.stats(decode=True, stream=True)

        return next(self._stats)

    def stop_stats_stream(self):
        self._stats = None

    def top(self, **kwargs):
        """
        Display the running processes of the container.

        Returns:
            (str): The output of the top

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.top(**kwargs)

    def update(self, **kwargs):
        """
        Update resource configuration of the containers.

        Returns:
            (dict): Dictionary containing a ``Warnings`` key.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.update(**kwargs)

    def wait(self, **kwargs):
        """
        Block until the container stops, then return its exit code. Similar to
        the ``docker wait`` command.

        Returns:
            (int): The exit code of the container. Returns ``-1`` if the API
            responds without a ``StatusCode`` attribute.

        Raises:
            :py:class:`requests.exceptions.ReadTimeout`
                If the timeout is exceeded.
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.wait(**kwargs)

    def logs(self, **kwargs):
        """
        Get logs from this container. Similar to the ``docker logs`` command.

        The ``stream`` parameter makes the ``logs`` function return a blocking
        generator you can iterate over to retrieve log output as it happens.

        Args:
            stdout (bool): Get ``STDOUT``
            stderr (bool): Get ``STDERR``
            stream (bool): Stream the response
            timestamps (bool): Show timestamps
            tail (str or int): Output specified number of lines at the end of
                logs. Either an integer of number of lines or the string
                ``all``. Default ``all``
            since (datetime or int): Show logs since a given datetime or
                integer epoch (in seconds)
            follow (bool): Follow log output

        Returns:
            (generator or str): Logs from the container.

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.logs(**kwargs)

    def recent_logs(self, stdout=True, stderr=True, lines=3):
        """
        Returns the most recent logs (given number of lines).

        :param stdout: Whether to show standart output (flag)
        :param stderr: Whether to show standard error output (flag)
        :param lines: Number of lines to show.
        :return: Recent log bytes.
        """
        return self.logs(stdout=stdout, stderr=stderr, tail=lines)

    def export(self):
        """
        Export the contents of the container's filesystem as a tar archive.

        Returns:
            (str): The filesystem tar archive

        Raises:
            :py:class:`docker.errors.APIError`
                If the dopq_server returns an error.
        """
        return self.container_obj.export()

    @property
    def gpu_minors(self):
        """
        Provides the GPU minors for given container object

        :return: Returns a list with GPU minors.
        """
        return self._gpu_minors

    @gpu_minors.setter
    def gpu_minors(self, minors):

        assert isinstance(minors, list), 'gpu minors must be provided as a list'
        assert all([isinstance(m, str) for m in minors]), 'gpu minors must have string values'

        self._gpu_minors = minors

    def append_new_logs(self):
        """
        Retrieves all updates since last check and writes it to log.
        :return: Number of new bytes
        """

        # get new logs
        new_logs = self.logs(stdout=True, stderr=True, since=self.last_log_update)

        # update
        self.last_log_update = int(time.time())

        # leave
        if len(new_logs) == 0:
            return 0

        # add to log
        LOG.info("Container '{}' status: ".format(self.name(), new_logs))

        # return the number of new bytes
        return len(new_logs)

    def append_new_logs_to_file(self, file_path=None):
        """
        Appends the newly created log data to given file path.

        :param file_path: Path for container log (if none, a name will be generated)
        :return: Number of new bytes
        """

        # if no file path has been given
        if file_path is None:
            # build file path
            file_path = os.path.join(self.log_dir, "{}_{}.log".format(self.name(), self.created_at))

        # get new logs
        new_logs = self.logs(stdout=True, stderr=True, since=self.last_log_file_update)

        # update
        self.last_log_file_update = int(time.time())

        # leave
        if len(new_logs) == 0:
            return 0

        # open in append mode and add
        with open(file_path, 'a+') as file_h:
            file_h.write(new_logs)

        # return the number of new bytes
        return len(new_logs)

    def container_stats(self, runtime_stats=True):
        """
        Provides information about container including also runtime info (if flag is set).

        :param runtime_stats: If true also actual hardware runtime info will be added.
        :return: String with container info.
        """

        self.reload()

        # build base info
        if self.container_obj is None:
            base_info = {'name': self.name, 'executor': self.executor, 'run_time': '',
                         'docker name': '', 'created': '', 'status': 'not built'}
        else:
            base_info = {'name': self.name, 'executor': self.executor, 'run_time': self.run_time,
                         'docker name': self.docker_name, 'created': self.created_at, 'status': self.status}

        # also show runtime info?
        if runtime_stats:

            # get stats
            stats_dict = self.stats

            # TODO: Extract cpu usage percentage (which seems to be a bit tricky..)
            # cpu_stats = stats_dict['cpu_stats']
            cpu = CPU(interval=0.1)
            cpu_usage_percentage = cpu.cpu_percent()  # changed this because psutil.cpu_percentage with interval is blocking
            cpu_usage_percentage = '{}%'.format(cpu_usage_percentage)

            # calc memory usage
            mem_stats = stats_dict['memory_stats']
            mem_usage = mem_stats.get('usage')
            if mem_usage is not None:
                mem_usage = '{}%'.format(round(mem_usage * 100.0 / mem_stats['limit'], 1))

            # add base runtime info
            base_info.update({'cpu': cpu_usage_percentage, 'memory': mem_usage})

            # add gpu info, if required
            if self.use_gpu:
                gpu_info = get_gpu_infos(self.gpu_minors)
                base_info['gpu'] = [
                    {'id': gpu_dt['id'], 'usage': round(gpu_dt['memoryUsed'] * 100.0 / gpu_dt['memoryTotal'], 1)}
                    for gpu_dt in list(gpu_info.values())]

        return base_info

    def history_info(self):
        """
        Returns information about the container, dedicated to build a history.
        :return: Container information string.
        """

        # version without hardware runtime information
        return self.container_stats(runtime_stats=False)

    def create_mounts(self):
        """
        converts string to docker.type.Mount objects, also automatically adds user folder to /outdir
        :param mount_list: list of docker mount strings (as given in the config.ini)
        :param user: user for whom the mounts are created
        :return: list of docker.types.Mount objects, same len as mount_list
        """
        mount_list = self.mounts

        if mount_list == ['']:
            return None

        mounts = []
        for mount in mount_list:

            # split mount string in source and target
            mount = mount.split(':')

            # append user folder to source if target is outdir
            if mount[1] == '/outdir':
                mount[0] = os.path.join(mount[0], self.executor)
            if not os.path.exists(mount[0]):
                os.makedirs(mount[0])

            # create Mount object and append to list
            mount = docker.types.Mount(source=mount[0], target=mount[1], type='bind')
            mounts.append(mount)

        return mounts

    def create_container(self):
        """
        create a docker container using a passed ContainerConfig object
        :param image: docker image on which the container will be based
        :param config: ContainerConfig object
        :param mounts: list of mount pairs (/dir:/dir)
        :param logger: instance of logging or colorlog
        :return: docker container
        """

        client = docker.from_env()
        create_conf = self.config.docker_params(image=self.image, detach=True, mounts=self.mounts,
                                                environment=[
                                                    "NVIDIA_VISIBLE_DEVICES=" + str(','.join(self.gpu_minors))])
        container = client.containers.create(**create_conf)
        self.container_id = container.id


if __name__ == '__main__':
    client = docker.from_env()
    json_str = '{"num_slots": 1, "num_gpus": 1, "required_memory": "32g", "run_params": {}, "executor_name": "ilja", "build_flag": true, "name": "3d-ae-naive"}'
    config = ContainerConfig.from_string(json_str)
    docker_container = client.containers.create('pt-base', 'sleep 60', environment=["NVIDIA_VISIBLE_DEVICES=none"])
    container = Container(config, docker_container)
    # container.set_gpu_minors(['0'])
    print((container.gpu_minors))
    time.sleep(1)
    container.start()
    print((container.gpu_minors))
    stats = container.container_stats()
