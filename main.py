#!/usr/bin/env python
import sys
import os.path
import shelve

'''Messed up hack for py2exe'''
if hasattr(sys, 'frozen'):
    workingdir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
    workingdir = os.path.dirname(sys.argv[0])

#sys.stdout = open('mxit.log', 'w')
#sys.stderr = open('mxit.err.log', 'w')
from Queue import Queue
import threading
import gobject

'''TODO: Remove dependency on twisted'''
from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except AssertionError:
    #We are most likely debugging
    pass
from twisted.internet import reactor

import gtk

from protocol.constants import COMMANDS
from protocol import commands
from protocol.commands import ClientMessage, SetMoodMessage
from protocol.mxitprotocol import MXitProtocolThread, parseServerMsg, socketBuildClientMessage 

from gui.applicationwindow import ApplicationWindow
from gui.activationwindow import ActivationWindow
from gui.loginwindow import LoginWindow
from gui.errordialog import errorDialog
#from gui.trayicon import TrayIcon
from sound import Sound

gtk.gdk.threads_init()

class MXit(dict):
    def __init__(self):
        #Create a dictionary that is persistant across all sessions
        
        #self.settings = Settings()
        self.settings = shelve.open('mxit.settings')

        self['windows'] = {}
        self['contactCallback'] = []

        self['connected'] = False
        self['loggedIn'] = False
        self['transport'] = 'socket'    #TODO: make HTTP work as well
        self['messageQueue'] = Queue()
        self['receivedMessageQueue'] = Queue()

        self.initialise()

    def initConnection(self):
        #Give default values if we don't have any settings
        hostname = self.settings['soc1'].split('//')[1].split(':')[0]
        port = 9119

        self.protocolThread = MXitProtocolThread(hostname, port, self)
        self.protocolThread.start()
        #self.protocolThread.run()

    def initialise(self):
        #self['tray'] = TrayIcon(self)
        self['sound'] = Sound(self)
        self['MainWindow'] = ApplicationWindow(self)
        if not self.settings.has_key('category'):
            self['ActivationWindow'] = ActivationWindow(self)
            pass
        else:
            self.initConnection()
            try:
                if self.settings['autoLogin']:
                    self.do_login()
                else:
                    LoginWindow(self)
            except:
                LoginWindow(self)
            #Not sure when I should take this out
            if self.settings['category'] == '0':
                #self.on_registerItem_activate(None)
                print 'Registration not complete!!'

    def handleMsg(self, data):
        '''Parses and handles received server messages '''
        originaldata = data
        if self['transport'] == 'socket':
            data = parseServerMsg(data)
        elif self['transport'] == 'http':
            pass

        try:
            command = int(data[0])
        except:
            log.err('For some reason we couldn\'t parse command: %s' % data)
            return
            
        try:
            errorCode = int(data[1])
            errorMessage = None
        except TypeError:
            errorCode = int(data[1][0])
            errorMessage = data[1][1]
            print errorCode, errorMessage
            gobject.timeout_add(0, errorDialog, errorMessage)
              
        #When dealing with chunks we shouldn't parse the message. Otherwise we get messed up
        #binary data
        if command == 27:
            message = originaldata.split('\0', 2)[2]
        else:
            message = data[2:]
          
        try:
            func = getattr(commands, "handle_%s" % COMMANDS[command])
            func(errorCode, errorMessage, message, self)
        except AttributeError:
            commands.handle_default(command, errorCode, message, errorMessage, self)
    
    def sendMsg(self, msg):
        if isinstance(msg, ClientMessage):
            print 'Attempting to send',msg.__class__
            if self['transport'] == 'socket':
                toBeSent = socketBuildClientMessage(self.settings['loginname'], msg.getMessage())
            elif self['transport'] == 'http':
                pass
            msg.messageSent()
        else:
            toBeSent = self._buildClientMessage(msg)

        self['messageQueue'].put(toBeSent)
        #self.protocolThread.send(toBeSent)
            
    def do_login(self, password=None):
        from protocol.commands import LoginMessage

        if password == None:
            try:
                password = self.settings['password']
            except KeyError:
                #If password isn't in settings this means that last time login failed. Show window instead
                #Password is actually stored in .settings['tempPassword']. Remove it because it is likely
                #incorrect
                del self.settings['tempPassword']
                LoginWindow(self)
                return
        
        #TODO: Allow user to select locale and language. No really... do this
        #I'm being for real now
        locale = 'en'
        loginMessage = LoginMessage(password, locale, self)
        self.sendMsg(loginMessage)
    
    def do_logout(self):
        from protocol.commands import LogoutMessage
        self.sendMsg(LogoutMessage(self))
        self.settings.close()
        #gobject.timeout_add(40*1000, gtk.main_quit)
    
    def do_keepalive(self):
        from protocol.commands import KeepAliveMessage
        self.sendMsg(KeepAliveMessage())
        gobject.timeout_add(480*1000, self.do_keepalive)
        return False

try:
    import ctypes
    libc = ctypes.CDLL('libc.so.6')
    libc.prctl(15,'MXitPC',0,0,0)
except:
    #ctypes only works on Unix
    pass

#Setup gtk theme
gtk.rc_parse(os.path.join('gtk-2.0', 'gtkrc'))
#Start application
MXit()
reactor.run()
