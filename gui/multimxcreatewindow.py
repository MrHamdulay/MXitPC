import gtk
import os.path

from protocol.constants import OFFLINE, CONTACT_TYPE_MXIT
from protocol.commands import CreateMultiMX
from gui.errordialog import errorDialog

class MultiMXCreateWindow:
    contactButtonList = []

    def __init__(self, mxit):
        self.mxit = mxit

        self.initGui()

    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'MultiMxCreate.glade'))
        dialog = self.builder.get_object('MultiMxCreateDialog')
        dialog.connect('response', self.on_response)
        
        container = self.builder.get_object('container')
        for contact in self.mxit['contactStore'].contactContactList.itervalues():
            if not contact.presence == OFFLINE and contact.contactType == CONTACT_TYPE_MXIT:
                contactobject = gtk.CheckButton(label=contact.nickname)
                contactobject.set_name(contact.contactAddress)
                contactobject.show()
                self.contactButtonList.append(contactobject)            
                container.add(contactobject)
        dialog.show()

    def on_response(self, dialog, response_id):
        if not response_id == 0:
            dialog.destroy()
            return
        contactlist = [self.mxit['contactStore'].contactContactList[button.get_name()] for button in self.contactButtonList if button.get_active()]
        if len(contactlist) == 0:
            errorDialog('Please select at least one contact')
            return
        groupname = self.builder.get_object('groupnameEntry').get_text()
        if len(groupname) == 0:
            errorDialog('Please create a name for your MultiMx')
            return
        dialog.destroy()
        message = CreateMultiMX(groupname, contactlist)
        self.mxit.sendMsg(message)
