# Copyright (C) 2012, 2013, 2014, 2015 Mike Mattice
#
# This file is part of txframed.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


class STXETXLongLineTester(STXETXBasicTester):
    MAX_LENGTH = 10

    def msgLengthExceeded(self, line):
        self.received.append(line)

class STXETXLongLinetestFactory(protocol.Factory):
    protocol = STXETXLongLineTester

class STXETXLongLineTestCase(STXETXBasicTestCase):
    factory = STXETXLongLinetestFactory

    def test_incoming(self):
        excessive = 'A' * (self.proto.MAX_LENGTH * 2 + 2)
        self.proto.dataReceived('\x02' +  excessive + '\x03')
        self.assertEqual(self.proto.received, ['\x02' + excessive[:self.proto.MAX_LENGTH]])


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
