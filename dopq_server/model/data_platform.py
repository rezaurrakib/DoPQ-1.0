import os
import Pyro4
import hashlib
import pickledb

##################### Data Platform class #####################
# Provides necessary wrapper accessed from the viewcontroller #
###############################################################

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


@Pyro4.expose
class DataPlatform():
    def __init__(self, pq_obj, provider_obj, config):
        self.dopq_wrp_obj = pq_obj
        self.provider_obj = provider_obj
        self.user_database_path = config['paths']['user_db']
        print("User_db_path : ", self.user_database_path)

    ############################# Container Info API's ##########################
    # These API's can only be accessible from viewcontroller class
    #
    #############################################################################

    def dopq_system_shutdown(self):
        print("About to shutdown")
        if self.provider_obj.status == "running":
            self.provider_obj.provider_stop()
        self.dopq_wrp_obj.terminating_flag = True
        self.dopq_wrp_obj.dopq_stop()

    def check_pass_encryption(self, password):
        # Encrypt the password
        encd = password.encode()
        res = hashlib.md5(encd)
        encrptd_pass = res.hexdigest()

        return encrptd_pass

    def check_user_validity(self, username, password):
        is_valid = False
        db = pickledb.load(self.user_database_path, False)

        if db.exists(username):
            encrp_pass = self.check_pass_encryption(password)
            if  encrp_pass == db.get(username):
                is_valid = True
        else:
            print("Username not exist in the DB.")

        return is_valid

    @property
    def get_running_info(self):
        run_cont_list = []  # A list of dictionary
        containers = self.dopq_wrp_obj.running_containers

        for c in containers:
            print("(Data Platform) --> Current running Container : ", c.container_stats())
            run_cont_list.append(c.container_stats())

        return run_cont_list

    @property
    def get_user_statistics(self):
        user_stats = self.dopq_wrp_obj.users_stats
        return user_stats

    @property
    def get_dopq_status(self):
        system_status = []
        dopq_stat = self.dopq_wrp_obj.status
        dopq_uptime = self.dopq_wrp_obj.uptime
        provider_stat = self.provider_obj.status
        provider_uptime = self.provider_obj.uptime

        #print("test: DoPQ Stat: ", self.dopq_wrp_obj.status)
        #print("test: DoPQ uptime: ", self.dopq_wrp_obj.uptime)
        #print("test: Provider Stat: ", self.provider_obj.status)
        #print("test: Provider Uptime: ", self.provider_obj.uptime)

        system_status.append(dopq_stat)
        system_status.append(dopq_uptime)
        system_status.append(provider_stat)
        system_status.append(provider_uptime)

        return system_status

    @property
    def get_completed_containers_info(self):
        history = []  # A list of dictionary

        containers = self.dopq_wrp_obj.history
        for c in containers:
            history.append(c.container_stats(runtime_stats=False))

        print("(Data Platform)--> history_list length: ", len(history))
        return history

    @property
    def get_enqueued_container_list(self):
        enq_list = []  # A list of dictionary

        containers = self.dopq_wrp_obj.container_list
        enq_list = [c.history_info() for c in containers]
        #print("(Data Platform)--> enqueued_containers : ", enq_list)
        print("(Data Platform)--> enqueued_containers length: ", len(enq_list))
        return enq_list

    def exec_dopq_lock_state(self, is_enqueue_update):
        """
        Lock the dopq process until the enqueued containers are updated from client pc
        :return:
        """
        if is_enqueue_update:
            self.dopq_wrp_obj.lock_update(True)
        else:
            self.dopq_wrp_obj.lock_update(False)

        print("(Data Platform)--> lock state: ", self.dopq_wrp_obj.lock_state)

    def update_enqueued_container_list(self, del_list):
        """
        Summary of the Function:
        ------------------------
        (a) Update/delete unwanted containers from the Enqueued List

        Parameters:
        -----------
        :arg: del_list is a dictionary
        :return: None
        """
        self.dopq_wrp_obj.cont_update_after_deletion(del_list)
        #print("after update the enqueued stats: ", self.get_enqueued_container_list)
        print("After update the enqueued stats Length: ", len(self.get_enqueued_container_list))
        self.exec_dopq_lock_state(False)

    def clear_dopq_history_list(self, usrname, pswd):
        """
        Summary of the Function:
        ------------------------
        (a) Delete previous history of completed docker containers and clear the history list

        Parameters:
        -----------
        :arg: Username, password of the valid user
        :return: None
        """

        self.dopq_wrp_obj.history = [] # Clear the current history list
        # Clear the history dill files, so next time, upon starting, system can have a fresh start
        path = os.path.join(self.dopq_wrp_obj.paths['history'], self.dopq_wrp_obj.history_file)
        print("Deleted history dill path: ", path)
        os.remove(path)
