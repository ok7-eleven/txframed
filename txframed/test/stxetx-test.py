from twisted.internet import protocol
from txframed.framed import STXETXProtocol

from twisted.trial import unittest
from twisted.test import proto_helpers

class STXETXBasicTester(STXETXProtocol):
    def connectionMade(self):
        self.received = []

    def msgReceived(self, line):
        self.received.append(line)

    def ACKReceived(self):
        self.received.append('ACK')

    def NAKReceived(self):
        self.received.append('NAK')

class STXETXBasictestFactory(protocol.Factory):
    protocol = STXETXBasicTester

class STXETXBasicTestCase(unittest.TestCase):
    factory = STXETXBasictestFactory
    def setUp(self):
        factory = self.factory()
        self.proto = factory.buildProtocol(('127.0.0.1', 0))
        self.tr = proto_helpers.StringTransport()
        self.proto.makeConnection(self.tr)

    def test_incoming(self):
        self.proto.dataReceived('\x02testcase1\x03\x06\x15')
        self.assertEqual(self.proto.received, ['testcase1', 'ACK', 'NAK'])

    def test_outgoing(self):
        self.proto.sendMsg('testcase5')
        self.assertEqual(self.tr.value(), '\x02testcase5\x03')


class STXETXStringLRCTester(STXETXBasicTester):
    lrc = '\x10'

    def lrcFail(self, msg, lrc):
        self.received.append('LRCFAIL')

class STXETXStringLRCtestFactory(protocol.Factory):
    protocol = STXETXStringLRCTester

class STXETXStringLRCTestCase(STXETXBasicTestCase):
    factory = STXETXStringLRCtestFactory

    def test_incoming(self):
        self.proto.dataReceived('\x02testcase')
        self.proto.dataReceived('2\x03\x10\x06\x15\x02testcase3\x03\x11')
        self.assertEqual(self.proto.received, ['testcase2', 'ACK',
                                               'NAK', 'LRCFAIL'])

    def test_outgoing(self):
        self.proto.sendMsg('testcase5')
        self.assertEqual(self.tr.value(), '\x02testcase5\x03\x10')


class STXETXCallableLRCTester(STXETXStringLRCTester):
    lrclen = 1
    def lrc(self, msg):
        return '?'

class STXETXCallableLRCtestFactory(protocol.Factory):
    protocol = STXETXCallableLRCTester

class STXETXCallableLRCTestCase(STXETXStringLRCTestCase):
    factory = STXETXCallableLRCtestFactory

    def test_callable(self):
        self.assertTrue(callable(self.proto.lrc))

    def test_incoming(self):
        self.proto.dataReceived('\x02testcase')
        self.proto.dataReceived('2\x03?\x06\x15\x02testcase3\x03\x11')
        self.assertEqual(self.proto.received, ['testcase2', 'ACK',
                                               'NAK', 'LRCFAIL'])

    def test_outgoing(self):
        self.proto.sendMsg('testcase5')
        self.assertEqual(self.tr.value(), '\x02testcase5\x03?')
