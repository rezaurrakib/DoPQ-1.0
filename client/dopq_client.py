import Pyro4
from client import interface_pipeline

__authors__ = "Md Rezaur Rahman"
__copyright__ = "Copyright 2019, The DopQ Project"
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Reza, Ilja, Markus"
__status__ = "Dev"


class Client(object):
    def __init__(self):
        self.server_obj = None

    def deamon_creation(self):
        #name_server = Pyro4.locateNS(host='10.167.183.156') # Server ip as host
        name_server = Pyro4.locateNS(host='localhost')  # Server ip, Change it according to your Machine's ip
        server_uri = name_server.lookup("remote_dopq")
        print("Server URI: ", server_uri)
        dopq_server_obj = Pyro4.Proxy(server_uri)
        print(dopq_server_obj.__dict__.keys())
        self.server_obj = dopq_server_obj
        return dopq_server_obj

    def view_thread_communicator(self, dopq_server_obj):
        view_thread_obj = interface_pipeline.qt_main(dopq_server_obj)


if __name__ == '__main__':
    client_obj = Client()
    server_obj = client_obj.deamon_creation()
    client_obj.view_thread_communicator(server_obj)
