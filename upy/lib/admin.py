import binascii
import os
import machine
import uipc


class AdminService(uipc.ServiceBase):

    def reset(self, port, msg):
        machine.reset()

    def put(self, port, msg):
        try:
            _, path, data = msg
            data = binascii.unhexlify(data)
            with open(path, 'wb') as f:
                f.write(data)
            print(path, '... updated.')
            port.success()
        except Exception as e:
            print(path, '... failed:', e)
            port.failure(str(e))

    def mkdir(self, port, msg):
        _, path = msg
        try:
            os.mkdir(path)
        except Exception as e:
            port.failure(str(e))
