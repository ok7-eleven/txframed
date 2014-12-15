from twisted.internet.protocol import Protocol

WAITFORSTART = 0
WAITFORETX = 1
WAITFORLRC = 2

STX = '\x02'
ETX = '\x03'
ACK = '\x06'
NAK = '\x15'

class STXETXProtocol(Protocol):
    """
    @cvar _lrc: Method to calculate LRC, a single byte for a fixed LRC, or None for no LRC

    @cvar MAX_LENGTH: The maximum length of a line to allow (If a
                      sent line is longer than this, the connection is dropped).
                      Default is 16384.
    """
    _lrc = None
    _state = WAITFORSTART
    MAX_LENGTH = 16384

    def __init__(self):
        self._buffer = []

    def _bufferToMsg(self):
        if not self.transport.disconnecting:
            msg = ''.join(self._buffer)
            self._buffer = []
            self.msgReceived(msg[1:-1])

    def _lrcFail(self, lrc):
        msg = ''.join(self._buffer)
        self._buffer = []
        self.lrcFail(msg, lrc)

    def lrcFail(self, msg, lrc):
        pass

    def dataReceived(self, data):
        """Translates bytes into messages, and calls msgReceived/ACKReceived."""
        for c in data:
            if self._state == WAITFORSTART:
                if c == STX:
                    self._buffer.append(c)
                    self._state = WAITFORETX
                elif c == ACK:
                    self.ACKReceived()
                elif c == NAK:
                    self.NAKReceived()
            elif self._state == WAITFORETX:
                self._buffer.append(c)
                if len(self._buffer) > self.MAX_LENGTH:
                    return self.msgLengthExceeded(''.join(self._buffer))
                if c == ETX:
                    if self._lrc is None:
                        self._bufferToMsg()
                        self._state = WAITFORSTART
                    else:
                        self._state = WAITFORLRC
            elif self._state == WAITFORLRC:
                if isinstance(self._lrc, str) and (len(self._lrc) == 1):
                    if c == self._lrc:
                        self._bufferToMsg()
                    else:
                        self._lrcFail(c)
                    self._state = WAITFORSTART
                elif callable(self._lrc):
                    if c == self._lrc(self._buffer):
                        self._bufferToMsg()
                    else:
                        self._lrcFail(c)
                    self._state = WAITFORSTART

    def msgReceived(self, line):
        """Override this for when each msg is received.
        """
        raise NotImplementedError

    def ACKReceived(self):
        """Override this for when each msg is received.
        """
        raise NotImplementedError
        
    def NAKReceived(self):
        """Override this for when each msg is received.
        """
        raise NotImplementedError

    def sendMsg(self, msg):
        """Sends a msg to the other end of the connection.
        """
        sendbuff = [ STX, ]
        sendbuff.extend(msg)
        sendbuff.append(ETX)
        if type(self._lrc) == type(''):
            sendbuff.append(self._lrc)
        elif type(self._lrc) == "<type 'function'>":
            sendbuff.append(self._lrc(sendbuff))
        return self.transport.writeSequence(sendbuff)

    def msgLengthExceeded(self, line):
        """Called when the maximum line length has been reached.
        Override if it needs to be dealt with in some special way.
        """
        return error.ConnectionLost('Line length exceeded')
