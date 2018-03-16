import socket

import uipc
from config.service_airterm import config

class AirtermService(uipc.ServiceBase):

    def on_accepted(self, port):
        # unregister must be called before socket.airterm,
        # because socket.airterm reset fd number of port.socket.
        uipc.manager.unregister(port)
        socket.airterm(port.socket)

def register():
    uipc.manager.register_server(config.port, AirtermService())
    return config.port
