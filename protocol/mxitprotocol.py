import socket
import threading
import gobject
import Queue
import select

from protocol.commands import ClientMessage
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

class MXitProtocol:
    _started = False
    _thread = None
    
    _messageQueue = Queue.Queue()

    receivedMessageHooks = []
    errorOccuredHooks = []
    
    def __init__(self, hostname, port, loginname):
        self._hostname = hostname
        self._port = port
        self._loginname = loginname

    def login(self, password=None):
        if password == None:
            raise RuntimeException('No password given')
        locale = 'en'
        message = LoginMessage(password, locale, None)
        self.send(message)

    def send(self, message):
        if isinstance(message, ClientMessage):
            data = socketBuildClientMessage(self._loginname, message.getMessage())
            message.messageSent()
        else:
            data = message
        self._messageQueue.put(data)


    def addReceivedMessageHook(self, function):
        self.receivedMessageHooks.append(function)

    def addErrorOccuredHook(self, function):
        self.errorOccuredHooks.append(function)

    def start(self):
        if self._started:
            return
        thread = MXitProtocolThread(self._hostname, self._port, self._messageQueue)
        thread.receivedMessageHooks = self.receivedMessageHooks
        thread.errorOccuredHooks = self.errorOccuredHooks
        thread.start()

    def stop(self):
        thread.dismiss()

class MXitProtocolThread(threading.Thread):
    connected = False
    daemon = True
    _dismiss = threading.Event()
    _buffer = None

    receivedMessageHooks = None
    errorOccuredHooks = None

    def __init__(self, hostname, port, messageQueue):
        threading.Thread.__init__(self, group=None)
        self.messageQueue = messageQueue

        self.hostname = hostname
        self.port = port

    def run(self):
        ''' Protocol thread runner, checks if their is data to be sent and/or received. Does appropriate actions '''
        self.connect()

        while True:
            message = ''

            ready_to_read, ready_to_write, errors = select.select([self.socket], [self.socket], [self.socket], 1)
            #TODO: Figure out what to do with errors
            if not errors == []:
                pass
            #If we have ready_to+read sockets, read from them
            for socket in ready_to_read:
                self.dataReceived(socket)

            #Check if we have been told to shutdown
            if self._dismiss.is_set():
                break

            #Check if we their are any messages to be sent and send them
            try:
                message = self.messageQueue.get(True, 1)
            except Queue.Empty:
                if message == '' or message == None:
                    continue
            except AttributeError:
                pass
            else:
                self.socket.sendall(message)

    def dismiss(self):
        self._dismiss.set()

    def connect(self):
        if self.connected:
            raise RuntimeException, 'Already connected'
        self.socket = socket.socket()
        try:
            self.socket.connect((self.hostname, self.port))
        except IOError:
            [gobject.idle_add(errFunction, "Unable to connect to MXit server", True) for errFunction in errorOccuredHooks]
            return

        self.connected = True

    def dataReceived(self, socket, *args):
        ''' Called when their is data on the socket. Adds data to buffer and attempts to parse it '''
        data = socket.recv(1024)
        #If we for some reason have received no data, simply return
        if len(data) == 0:
            return True
        #Add data to buffer
        if not self._buffer == None:
            self._buffer += data
        else:
            self._buffer = data
            
        #Parse data
        self._parseData()
        return True

    def _parseData(self):
        pos = self._buffer.find('ln=')
        #If we can't find length header just return
        if pos == -1:
            return
        #Remove length header
        self._buffer = self._buffer[pos:]
        #Get length of current message
        try:
            self._length_end = self._buffer.find('\0')
            self._length = int(self._buffer[3:self._length_end])
        except ValueError:
            self._length = -1
            self._length_end = -1
            
        #Check if we have full message from length header, if we don't wait until we do
        if not (len(self._buffer[self._length_end+1:]) >= self._length):
            return
        
        #Get all data in this message
        data = self._buffer[self._length_end+1:self._length+self._length_end+1]
        #Check if we got proper data, if not just clear the buffer. this shouldn't be happening very often
        if len(data) == 0:
            self._buffer = ''
            return
        
        #Remove the last character if it's a nonsense character
        if data[-1] in '\0\1':
            data = data[:-1]

        #Remove current message from buffer
        self._buffer = self._buffer[self._length_end+self._length+1:]
        #Set temp variables to default
        self._length = -1
        self._length_end = -1
        
        #Call message received hooks
        [gobject.idle_add(function, data) for function in self.receivedMessageHooks]

        #If their is more data in the buffer, attempt to parse it
        if len(self._buffer):
            self._parseData()
        
    def _handleMessage(self, message):
        data = parseServerMsg(message)
        command = int(data[0])

        try:
            error_code = int(data[1][0])
            error_message = data[1][1]
            [gobject.idle_add(errFunction, "%d: %s" % (error_code, error_message)) for errFunction in errorOccuredHooks]
            return
        except TypeError:
            #We don't have an error Yay!
            pass

        if command == 27:
            data = message.split('\0', 2)[2]
        else:
            data = data[2:]
