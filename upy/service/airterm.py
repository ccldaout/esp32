import socket

import mipc
from config.service_airterm import config

class AirtermService(mipc.ServiceBase):

    def on_accepted(self, port):
        # unregister must be called before socket.airterm,
        # because socket.airterm reset fd number of port.socket.
        mipc.manager.unregister(port)
        port.socket.airterm()

def register():
    mipc.manager.register_server(config.port, AirtermService())
    return config.port
