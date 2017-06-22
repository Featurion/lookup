import srp

from src.base import constants, utils
from src.base.Datagram import Datagram
from src.users.ClientBase import ClientBase


class ClientAI(ClientBase):

    def __init__(self, server, address, port):
        ClientBase.__init__(self, address, port)
        self.server = server

    def stop(self):
        """Handle stopping of the client"""
        self.server.cm.removeClient(self)
        ClientBase.stop(self)

    def sendOK(self):
        self.sendResp(True)

    def sendNo(self):
        self.sendResp(False)

    def sendError(self, title, err):
        datagram = Datagram()
        datagram.setCommand(constants.CMD_ERR)
        datagram.setSender(self.getId())
        datagram.setRecipient(self.getId())
        datagram.setData((title, err))

        self.sendDatagram(datagram)

    def handleReceivedDatagram(self, datagram):
        datagram = ClientBase.handleReceivedDatagram(self, datagram)

        if not datagram:
            return

        if datagram.getCommand() == constants.CMD_REQ_CONNECTION:
            self.doHandshake(datagram)
        elif datagram.getCommand() == constants.CMD_REQ_LOGIN:
            self.doLogin(datagram)
        elif datagram.getCommand() == constants.CMD_REQ_CHALLENGE:
            self.doChallenge(datagram)
        elif datagram.getCommand() == constants.CMD_REQ_CHALLENGE_VERIFY:
            self.doChallengeVerification(datagram)
        elif datagram.getCommand() == constants.CMD_HELO:
            self.doHelo(datagram)
        elif datagram.getRecipient() in self.zm.getZoneIds():
            self.forwardZoneMessage(datagram)
        else:
            self.notify.warning('received suspicious datagram')

    def doHandshake(self, datagram):
        """Respond to an initiated handshake"""
        self.generateSecret(datagram.getData())
        self.notify.debug('received public key')

        self.sendResp(self.getKey())
        self.notify.debug('sent public key')

        self.setSecure(True)

    def doLogin(self, datagram):
        name, mode = datagram.getData()
        self.notify.info('{0} attempting to log in'.format(name))

        if utils.isNameInvalid(name):
            self.notify.debug('name is invalid')
            self.sendNo()
        else: # valid name
            self.notify.debug('name is valid')

        client_hmac = datagram.getHMAC()
        server_hmac = self.generateHmac(name.encode(), constants.HMAC_KEY, True)
        if server_hmac != client_hmac:
            self.notify.warning('received suspicious improper hmac')
            self.sendNo()
            return
        else: # valid hmac
            self.notify.debug('HMAC matches')
            self.setName(name)
            self.setMode(mode)
            self.server.cm.addClient(self)
            self.sendOK()

    def doChallenge(self, datagram):
        self.notify.debug('challenging')
        salt, vkey = srp.create_salted_verification_key(self.getName().encode(),
                                                        constants.HMAC_KEY)

        self.svr = srp.Verifier(self.getName().encode('latin-1'),
                                salt,
                                vkey,
                                bytes.fromhex(datagram.getData()))
        s, B = self.svr.get_challenge()

        if s is None or B is None:
            self.notify.warning('suspicious challenge failure')
            self.sendNo() # initial challenge response
            return
        else:
            self.notify.debug('challenge success')
            self.sendResp([s.hex(), B.hex()])

    def doChallengeVerification(self, datagram):
        self.notify.debug('verifying')
        M = bytes.fromhex(datagram.getData())
        if M:
            HAMK = self.svr.verify_session(M)
            if HAMK and self.svr.authenticated(): # authenticated
                self.notify.debug('challenge verified')
                self.sendResp(HAMK.hex())
            else:
                self.notify.warning('suspicious challenge failure')
                self.sendNo()

    def doHelo(self, datagram):
        ai = self.server.zm.addZone(self, *datagram.getData())
        if ai is None:
            self.sendError(constants.TITLE_NAME_DOESNT_EXIST,
                           constants.NAME_DOESNT_EXIST)
            return
        else:
            ai.sendHelo()

    def forwardZoneDatagram(self, datagram):
        ai = self.server.zm.getZoneById(datagram.getRecipient())
        ai.receiveDatagram(datagram)
