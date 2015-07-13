from twisted.internet import protocol
from txframed.stxetx import STXETXProtocol

from twisted.trial import unittest
from twisted.test import proto_helpers

class STXETXTester(STXETXProtocol):
    def connectionMade(self):
        print "connection made"
        self.received = []

    def lrcFail(self, msg, lrc):
        pass

    def msgReceived(self, line):
        self.received.append(line)

    def ACKReceived(self):
        self.received.append('ACK')

    def NAKReceived(self):
        self.received.append('NAK')


class STXETXtestFactory(protocol.Factory):
    protocol = STXETXTester

class STXETXTestCase(unittest.TestCase):
    def setUp(self):
        factory = STXETXtestFactory()
        self.proto = factory.buildProtocol(('127.0.0.1', 0))
        print self.proto
        self.tr = proto_helpers.StringTransport()
        self.proto.makeConnection(self.tr)

    def test_incoming(self):
        self.proto.dataReceived('\x02testcase1\x03\x06\x15')
        self.assertEqual(self.proto.received, ['testcase1', 'ACK', 'NAK'])
