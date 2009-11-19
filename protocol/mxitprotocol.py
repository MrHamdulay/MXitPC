import socket
import threading
import gobject
import Queue
import select

from gui.errordialog import errorDialog

def parseServerMsg(msg):
    ''' Parse the message the server sends us and it to a list '''
    temp = []
    for i in msg.split('\0'):
        if '\1' in i:
            temp.append(i.split('\1'))
        else:
            temp.append(i)
    
    return temp

def socketBuildClientMessage(loginname, msgArgs):
    #Todo: separate this into TCP adapter
    cm, ms = msgArgs
    
    if not isinstance(ms, str) and not ms == None:
        ms = '\1'.join([str(item) for item in ms])

    message = 'id=%s\0cm=%d' % (loginname, int(cm))
    if not ms == None:
        message += '\0ms=%s' % ms
    
    message = 'ln=%d\0%s' % (len(message), message)
    return message 

class MXitProtocolThread(threading.Thread):
    def __init__(self, hostname, port, mxit):
        threading.Thread.__init__(self, group=None)
        self.daemon = True
        self.mxit = mxit
        self.messageQueue = self.mxit['messageQueue']
        self._dismiss = threading.Event()

        self.hostname = hostname
        self.port = port

    def dismiss(self):
        self._dismiss.set()

    def run(self):
        print 'Protocol thread started'
        protocol = MXitProtocol(Queue.Queue(), self.mxit)
        protocol.connect(self.hostname, self.port)

        while True:
            message = ''

            ready_to_read, ready_to_write, errors = select.select([protocol.socket], [protocol.socket], [protocol.socket], 1)
            if not errors == []:
                pass
            for socket in ready_to_read:
                protocol.dataReceived(socket)

            if self._dismiss.is_set():
                break

            try:
                message = self.messageQueue.get(True, 1)
            except Queue.Empty:
                if message == '' or message == None:
                    continue
            except AttributeError:
                pass
            else:
                if self._dismiss.is_set():
                    self.messageQueue.put(message, True, 1)
                protocol.send(message)

class MXitProtocol:
    '''Don't know how I am going to do HTTP requiests don't think I can use an adapter
    Think about maybe not using twisted library for that. But then there is going to be
    lots of redundancy on lots of stuff '''
    
    _buffer = None

    def __init__(self, receivedMessagesQueue, mxit):
        self.connected = False
        self.receivedMessagesQueue = receivedMessagesQueue
        self.mxit = mxit

    def connect(self, hostname, port):
        if self.connected:
            raise RuntimeException, 'Already connected'
        self.socket = socket.socket()
        try:
            self.socket.connect((hostname, port))
        except IOError:
            gobject.idle_add(lambda: errorDialog('Unable to connect to MXit server.', True))

        self.mxit['connected'] = True
        self.connected = True

        #gobject.io_add_watch(self.socket, gobject.IO_IN, self.dataReceived)
        #gobject.io_add_watch(self.socket, gobject.IO_HUP, self.lostConnection)

    def lostConnection(self, socket, condition):
        print 'Lost connection to MXit'
        errorDialog('Connection to mxit lost. Reconnecting')
        
    def dataReceived(self, socket, *args):
        data = socket.recv(1024)
        if len(data) == 0:
            return True
        if not self._buffer == None:
            self._buffer += data
        else:
            self._buffer = data
            
        self._parseData()
        return True
        
    def _parseData(self):
        pos = self._buffer.find('ln=')
        if pos == -1:
            #Not supposed to happen
            return
        self._buffer = self._buffer[pos:]
        try:
            self._length_end = self._buffer.find('\0')
            self._length = int(self._buffer[3:self._length_end])
        except ValueError:
            self._length = -1
            self._length_end = -1
            
        if not (len(self._buffer[self._length_end+1:]) >= self._length):
            #Message not fully received yet
            return
        
        ''' You may be tempted to remove the 1 at the end of this...
        DONT!! Otherwise the last byte of every text message will be removed.
        On most messages this is \0 but on text messages it could be an important
        character '''
        data = self._buffer[self._length_end+1:self._length+self._length_end+1]
        if len(data) == 0:
            self._buffer = ''
            return
        
        if data[-1] in '\0\1':
            data = data[:-1]

        self._buffer = self._buffer[self._length_end+self._length+1:]
        self._length = -1
        self._length_end = -1
        
        #If using one thread doesn't work create another one to handle all this shit
        #self.receivedMessagesQueue.put(data, True, 5)
        self.mxit.handleMsg(data)
        #gobject.idle_add(self.mxit.handleMsg, data)
        if len(self._buffer):
            self._parseData()
        
    def send(self, data):
        print 'sending data'
        self.socket.sendall(data)
