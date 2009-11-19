'''
Created on May 17, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import pango
import os.path

from twisted.python import log

from protocol.commands import AcceptInviteMessage, RejectInviteMessage, BlockInviteMessage
from protocol.constants import * 

class InvitationWindow:
    groupButtonList = []

    def __init__(self, data, mxit):
        self.mxit = mxit
        
        #Play alert
        self.mxit['sound'].invite_received()

        #Retrieve invitation data
        self.contactAddress, self.nickname, self.type, self.hiddenloginname, self.invitemsg, self.groupchatmod = data

        self.initGui()

    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'InviteWindow.glade'))
        dialog = self.builder.get_object('InviteDialog')

        if self.hiddenloginname == '0':
            self.builder.get_object('numberEntry').set_text(self.contactAddress)
        else:
            self.builder.get_object('numberEntry').set_text('Number hidden')

        if int(self.type) == CONTACT_TYPE_MXIT:
            dialog.set_title('Invitation to chat with %s' % self.nickname)
            self.builder.get_object('inviteeEntry').set_text(self.nickname)
        elif int(self.type) == CONTACT_TYPE_MULTIMIX:
            dialog.set_title('Invitation to MultiMx %s' % self.nickname)
            self.builder.get_object('itviteeEntry').set_text(self.groupchatmod)

        if not self.invitemsg == '':
            label = gtk.Label(self.invitemsg)
            label.show()
            self.builder.get_object('container').add(label)

        for group in self.mxit['contactStore'].groupList.iterkeys():
            groupbutton = gtk.RadioButton('groupSelect', group)
            groupbutton.set_name(group)
            groupbutton.show()
            self.builder.get_object('groupContainer').add(groupbutton)
            self.groupButtonList.append(groupbutton)

        dialog.connect('response', self.on_response)
        dialog.show()
        
    def on_response(self, dialog, response_id, userdata=None):
        if response_id == gtk.RESPONSE_DELETE_EVENT:
            return
        dialog.destroy()
        #if accepted
        if response_id == 0:
            groupname = ''
            for button in self.groupButtonList:
                if button.get_active():
                    groupname = button.get_name()
                    break
            #Todo: add group support
            nickname = self.builder.get_object('inviteeEntry').get_text()
            message = AcceptInviteMessage(self.contactAddress, groupname, nickname)
        #if rejected
        elif response_id == 1:
            message = RejectInviteMessage(self.contactAddress)
        #if blocked
        elif response_id == 2:
            message = BlockInviteMessage(self.contactAddress)
            
        self.mxit.sendMsg(message)
