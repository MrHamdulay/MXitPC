#!/usr/bin/env python
#import sys
import os.path
import shelve
import gobject

#Messed up hack for py2exe
'''if hasattr(sys, 'frozen'):
    working_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
    working_dir = os.path.dirname(sys.argv[0])'''

#TODO: Implement proper logging
import sys
#sys.stdout = open('mxit.log', 'w')
#sys.stderr = open('mxit.err.log', 'w')

'''TODO: Remove dependency on twisted'''
from twisted.internet import gtk2reactor
try:
    gtk2reactor.install()
except AssertionError:
    pass
from twisted.internet import reactor

import gtk

from protocol.constants import COMMANDS
from protocol import commands
from protocol.mxitprotocol import MXitProtocol, parseServerMsg

from gui.applicationwindow import ApplicationWindow
from gui.activationwindow import ActivationWindow
from gui.loginwindow import LoginWindow
from gui.errordialog import errorDialog
from sound import Sound

gtk.gdk.threads_init()

import traceback

class MXit:
    ''' Main application class, everything is stored and happens through here '''
    def __init__(self):
        self.settings = shelve.open('mxit.settings')

        self.windows = {}
        self.contact_callback = []

        self.connected = False
        self.logged_in = False
        self.transport = 'socket'    #TODO: make HTTP work as well
        self.protocol = None

        self.sound = Sound(self)
        self.main_window = ApplicationWindow(self)
        self.MainWindow = self.main_window
        if not self.settings.has_key('category'):
            self.activation_window = ActivationWindow(self)
        else:
            self.init_connection()
            try:
                if self.settings['autoLogin']:
                    self.do_login()
            except Exception, e:
                e.printStackTrace()
                LoginWindow(self)

    def tempErr(self, message):
        print 'Error occured: ', message 

    def init_connection(self):
        #Give default values if we don't have any settings
        hostname = self.settings['soc1'].split('//')[1].split(':')[0]
        port = 9119

        self.protocol = MXitProtocol(hostname, port, self.settings['loginname'])
        self.protocol.addReceivedMessageHook(self.handleMsg)
        self.protocol.addErrorOccuredHook(self.tempErr)
        self.protocol.start()


    def handleMsg(self, data):
        '''Parses and handles received server messages '''
        original_data = data
        if self.transport == 'socket':
            data = parseServerMsg(data)
        elif self.transport == 'http':
            pass

        try:
            command = int(data[0])
        except:
            print 'For some reason we couldn\'t parse command: ', data
            return
            
        try:
            error_code = int(data[1])
            error_message = None
        except TypeError:
            error_code = int(data[1][0])
            error_message = data[1][1]
            print error_code, error_message
            gobject.timeout_add(0, errorDialog, errorMessage)
              
        #When dealing with chunks we shouldn't parse the message. Otherwise we get messed up
        #binary data
        if command == 27:
            message = original_data.split('\0', 2)[2]
        else:
            message = data[2:]
          
        try:
            func = getattr(commands, "handle_%s" % COMMANDS[command])
            func(error_code, error_message, message, self)
        except AttributeError:
            commands.handle_default(command, error_code, message, error_message, self)
    
    def send_message(self, msg):
        self.protocol.send(msg)

    def sendMsg(self, msg):
        self.protocol.send(msg)
            
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
        self.send_message(loginMessage)
    
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
    libc.prctl(15, 'MXitPC', 0, 0, 0)
except:
    #ctypes only works on Unix
    pass

#Setup gtk theme
gtk.rc_parse(os.path.join('gtk-2.0', 'gtkrc'))
#Start application
MXit()
reactor.run()
