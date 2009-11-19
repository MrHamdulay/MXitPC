'''
Created on May 19, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk
import pango

import os.path

from protocol.commands import InviteMessage 
from gui.errordialog import errorDialog

class AddUserWindow:
    def __init__(self, mxit):
        self.mxit = mxit
        
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'AddUserDialog.glade'))
        
        self.nicknameEntry = self.builder.get_object('nicknameEntry')
        self.contactAddressEntry = self.builder.get_object('numberEntry')
        self.inviteMessageEntry = self.builder.get_object('messageEntry')
        
        self.dialog = self.builder.get_object('AddUserDialog')
        self.dialog.connect('response', self.on_response_activate)
        #Todo: parse Group list and add it to the dialog
        self.dialog.show()
        
    def on_response_activate(self, dialog, response_id, *args):
        if not response_id == 1:
            dialog.destroy()
            return
        contactAddress = self.contactAddressEntry.get_text()
        if not len(contactAddress):
            errorDialog('Please enter cellphone number to invite')
            
        nickname = self.nicknameEntry.get_text()
        #Todo: Check whether this nickname exists
        if not len(nickname):
            errorDialog('Please enter nickname for contact')
        #Todo: add support for groups

        inviteMessage = self.inviteMessageEntry.get_text()
        
        #Type is always 0, MXit
        message = InviteMessage(contactAddress, nickname, inviteMessage)
        self.mxit.sendMsg(message)
        
        self.dialog.destroy()
