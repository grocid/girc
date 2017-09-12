import string

from twisted.internet import gtk3reactor
from twisted.words.protocols import irc
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl

class Client(irc.IRCClient):

    interface = None

    def signedOn(self):
        for c in self.factory.channels:
            self.join(c)

    def joined(self, channel):
        self.interface.add_channel(channel)

    def left(self, channel):
        self.interface.leave_channel(channel)        

    def privmsg(self, user, channel, msg):
        # Check if private message
        user = user.split("!")[0]

        if channel == self.nickname:
            self.interface.update_chat(user, user, msg)
        else:
            self.interface.update_chat(user, channel, msg)

class ClientFactory(protocol.ClientFactory):

    protocol = Client

    def __init__(self, channels, nickname, password, interface):
        self.nickname = nickname
        self.password = password
        self.channels = channels
        self.interface = interface
        self.client = None

    def buildProtocol(self, addr):
        self.client = Client()
        self.client.nickname = self.nickname
        self.client.password = self.password
        self.client.interface = self.interface
        self.client.factory = self
        return self.client

    def clientConnectionLost(self, connector, reason):
        print "Connection lost. Reason: %s" % reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed. Reason: %s" % reason