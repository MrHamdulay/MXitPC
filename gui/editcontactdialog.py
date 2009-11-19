'''
Created on May 23, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk
import pango

import os.path

from protocol.commands import UpdateContactInfoMessage

class EditContactDialog:
    group = ''
    def __init__(self, contactAddress, nickname, mxit):
        self.mxit = mxit
        self.contactAddress = contactAddress
        self.nickname = nickname
        
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'EditContactDialog.glade'))
        
        self.nicknameEntry = self.builder.get_object('nicknameEntry')
        self.nicknameEntry.set_text(self.nickname)
        self.contactAddressEntry = self.builder.get_object('numberEntry')
        self.contactAddressEntry.set_text(self.contactAddress)
        groupBox = self.builder.get_object('groupBox')
        noneGroupButton = self.builder.get_object('noneGroupButton')
        noneGroupButton.connect('toggled', self.groupButtonsCallback, '')
        
        for group in self.mxit['contactStore'].groupList.iterkeys():
            button = gtk.RadioButton(group=noneGroupButton, label=group)
            button.connect('toggled', self.groupButtonsCallback, group)
            button.show()
            groupBox.add(button)
        
        self.dialog = self.builder.get_object('EditContactDialog')
        self.dialog.connect('response', self.on_response_activate)
        self.dialog.show()
        
    def groupButtonsCallback(self, widget, group):
        if widget.get_active():
            self.group = group
        print group, self.group
        
    def on_response_activate(self, dialog, response_id, *args):
        if not response_id == 0:
            return
        contactAddress = self.contactAddressEntry.get_text()
        nickname = self.nicknameEntry.get_text()
        #Todo: add group support
        
        message = UpdateContactInfoMessage(contactAddress, nickname, self.group)
        self.mxit.sendMsg(message)
        
        self.mxit['contactStore'].updateRow(contactAddress, nickname, self.group)
        
        self.dialog.destroy()
