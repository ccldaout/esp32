import socket

import uipc
from config.service_airterm import config

class AirtermService(uipc.ServiceBase):

    def on_accepted(self, port):
        socket.airterm(port.socket)
        uipc.manager.unregister(port)

def register():
    uipc.manager.register_server(config.port, AirtermService())
    return config.port
