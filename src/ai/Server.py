import socket
import ssl
import sys

from src.ai.ClientManagerAI import ClientManagerAI
from src.ai.ZoneManagerAI import ZoneManagerAI
from src.base.Notifier import Notifier


class Server(Notifier):

    def __init__(self, address, port):
        Notifier.__init__(self)
        self.__socket = None
        self.__address = address
        self.__port = port
        self.__wantSSL = False

    def start(self):
        self.__connect()
        self.startManagers()
        self.waitForClients()

    def stop(self):
        if self.__socket is not None:
            try:
                self.notify.info('stopping server...')
                self.__socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                self.notify.critical('failed to stop server, socket is already closed')
                pass
            finally:
                self.__socket = None

        self.notify.info('server stopped!')
        sys.exit(0)

    def accept(self):
        return self.__socket.accept()

    def __supportSSL(self, socket_):
        return ssl.wrap_socket(self.__socket,
                               server_side=True,
                               keyfile='certs/ca.key',
                               certfile='certs/ca.crt',
                               cert_reqs=ssl.CERT_NONE,
                               ssl_version=ssl.PROTOCOL_TLSv1_2,
                               ciphers='ECDHE-RSA-AES256-GCM-SHA384',
                               do_handshake_on_connect=True)

    def __connect(self):
        try:
            self.notify.info('starting server...')
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if self.__wantSSL:
                self.__socket = self.__supportSSL(self.__socket)

            self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__socket.bind((self.__address, self.__port))
            self.__socket.listen(0) # refuse unaccepted connections
            self.notify.info('server online!')
        except Exception as e:
            self.notify.critical(str(e))

    def startManagers(self):
        self.client_manager = ClientManagerAI(self)
        self.zone_manager = ZoneManagerAI(self.client_manager)

    def waitForClients(self):
        while True:
            try:
                ai = self.client_manager.acceptClient()
                ai.start()
                self.notify.debug('client {0} joined!'.format(ai.getId()))
            except KeyboardInterrupt:
                self.notify.error('KeyboardInterrupt',
                                  'server killed while waiting for clients')
                break
            except Exception as e:
                self.notify.error(str(e))
                break
