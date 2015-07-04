from twisted.internet.protocol import Protocol
from twisted.internet import error

WAITFORSTART = 0
WAITFOREND = 1
WAITFORLRC = 2

STX = '\x02'
ETX = '\x03'
ACK = '\x06'
NAK = '\x15'

class FramedProtocol(Protocol):
    """
    @cvar lrc: Method to calculate LRC, a string for a fixed LRC, or None for no LRC

    @cvar MAX_LENGTH: The maximum length of a line to allow (If a
                      sent line is longer than this, the connection is dropped).
                      Default is 16384.
    """
    start, end, ack, nak = None, None, None, None
    lrc, lrclen = None, None
    _state = WAITFORSTART
    MAX_LENGTH = 16384

    def __init__(self):
        self._buffer = []
        self._lrcbuff = []

    def _bufferToMsg(self):
        if not self.transport.disconnecting:
            msg = ''.join(self._buffer)
            self._buffer, self._lrcbuff = [], []
            self.msgReceived(msg[1:-1])

    def _lrcFail(self, rlrc):
        msg = ''.join(self._buffer)
        self._buffer, self._lrcbuff = [], []
        self.lrcFail(msg, rlrc)

    def lrcFail(self, msg, rlrc):
        pass

    def dataReceived(self, data):
        """Translates bytes into messages, and calls msgReceived/ACKReceived."""
        for c in data:
            if self._state == WAITFORSTART:
                if c == self.start:
                    self._buffer.append(c)
                    self._state = WAITFOREND
                elif c == self.ack:
                    self.ACKReceived()
                elif c == self.nak:
                    self.NAKReceived()
            elif self._state == WAITFOREND:
                self._buffer.append(c)
                if len(self._buffer) > self.MAX_LENGTH:
                    return self.msgLengthExceeded(''.join(self._buffer))
                if c == self.end:
                    if self.lrc is None:
                        self._bufferToMsg()
                        self._state = WAITFORSTART
                    else:
                        self._state = WAITFORLRC
            elif self._state == WAITFORLRC:
                self._lrcbuff.append(c)
                if isinstance(self.lrc, str) and (len(self.lrc) == len(self._lrcbuff)):
                    rlrc = ''.join(self._lrcbuff)
                    if rlrc == self.lrc:
                        self._bufferToMsg()
                    else:
                        self._lrcFail(rlrc)
                    self._state = WAITFORSTART
                elif callable(self.lrc) and (self.lrclen == len(self._lrcbuff)):
                    rlrc = ''.join(self._lrcbuff)
                    if rlrc == self.lrc(self._buffer):
                        self._bufferToMsg()
                    else:
                        self._lrcFail(rlrc)
                    self._state = WAITFORSTART

    def msgReceived(self, line):
        """Override this for when each msg is received.
        """
        raise NotImplementedError

    def ACKReceived(self):
        """Override this for when an acknowledgement is received.
        """
        pass

    def NAKReceived(self):
        """Override this for when a negative acknowledgement is received.
        """
        pass

    def sendMsg(self, msg):
        """Sends a msg to the other end of the connection.
        """
        sendbuff = [ self.start, ]
        sendbuff.extend(msg)
        sendbuff.append(self.end)
        if isinstance(self.lrc, str):
            sendbuff.append(self.lrc)
        elif callable(self.lrc):
            sendbuff.append(self.lrc(sendbuff))
        return self.transport.writeSequence(sendbuff)

    def msgLengthExceeded(self, line):
        """Called when the maximum line length has been reached.
        Override if it needs to be dealt with in some special way.
        """
        return error.ConnectionLost('Line length exceeded')

class STXETXProtocol(FramedProtocol):
    start = STX
    end = ETX
    ack = ACK
    nak = NAK
