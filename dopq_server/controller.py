import os
import time
import Pyro4

from dopq_server.model import provider
from dopq_server.model import docker_pq_model
from dopq_server.model.model_helper import ModelHelper
from dopq_server.model.data_platform import DataPlatform

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


@Pyro4.expose
class DopqController():
    def __init__(self):
        self.configfile = 'config.ini'
        # get settings from config
        if not os.path.isfile(self.configfile):
            ModelHelper.write_default_config(self.configfile)

        self.config = ModelHelper.parse_config(self.configfile)
        self.dp_obj = None
        self.server_deamon = None

    def system_start(self):
        pq_obj = docker_pq_model.DopQContainer()
        provider_obj = provider.Provider(self.config, pq_obj.queue)  # Initiate Provider
        try:
            pvd_pid = provider_obj.start_provider()
            time.sleep(5)
            pq_obj.start_dopq_process()
            print("Provider pid: ", pvd_pid)

            self.dp_obj = DataPlatform(pq_obj, provider_obj, self.config)
            self.dp_obj.get_dopq_status
            self.remote_connection_starter(self.dp_obj)
        finally:
            self.server_deamon.close()
            self.dp_obj.dopq_system_shutdown()

    def remote_connection_starter(self, dp_obj):
        #Pyro4.config.HOST = "10.167.183.156" # dopq_server ip as host
        #Pyro4.config.NS_PORT = 9090
        self.server_deamon = Pyro4.Daemon()
        nameserver = Pyro4.locateNS()
        uri = self.server_deamon.register(self)
        nameserver.register("remote_dopq", uri)
        print("Server URI is : ", uri)
        self.server_deamon.requestLoop()


    # Series of exposed methods
    # These methods will be used for displaying/sending info against specific user request
    @property
    def get_running_containers_info(self):
        return self.dp_obj.get_running_info

    @property
    def get_containers_history_info(self):
        return self.dp_obj.get_completed_containers_info

    @property
    def get_enqueued_containers_info(self):
        return self.dp_obj.get_enqueued_container_list

    @property
    def get_dopq_system_status(self):
        return self.dp_obj.get_dopq_status

    @property
    def get_dopq_user_statistics(self):
        return self.dp_obj.get_user_statistics

    def dopq_system_lock(self, lock_state):
        self.dp_obj.exec_dopq_lock_state(lock_state)

    def delete_req_enqueued_containers(self, deleted_list):
        self.dp_obj.update_enqueued_container_list(deleted_list)

    def clear_dopq_history(self, user_info):
        is_valid = self.dp_obj.check_user_validity(user_info[0], user_info[1])
        if is_valid:
            self.dp_obj.clear_dopq_history_list(user_info[0], user_info[1])

    def shutdown_queue(self, user_info):
        is_valid = self.dp_obj.check_user_validity(user_info[0], user_info[1], db)
        if is_valid:
            print("System is about to shut down ....")
            self.dp_obj.dopq_system_shutdown()
            self.server_deamon.close()


if __name__ == "__main__":
    controller_obj = DopqController()
    controller_obj.system_start()
