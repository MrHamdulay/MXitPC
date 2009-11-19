'''
Created on May 23, 2009

@author: Yaseen
'''
import gtk
import os.path

from gui.errordialog import errorDialog

class AddGroupDialog:
    def __init__(self, mxit):
        self.mxit = mxit
        
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'NewGroupDialog.glade'))
        
        self.groupEntry = self.builder.get_object('nameEntry')
        
        self.dialog = self.builder.get_object('CreateGroupDialog')
        self.dialog.connect('response', self.on_response_activate)
        self.dialog.show()
        
    def on_response_activate(self, dialog, response_id, *args):
        if not response_id == 1:
            dialog.destroy()
            return
            
        group = self.groupEntry.get_text()
        if group == '' or group == None:
            errorDialog('Please enter a group name')
            return
        self.mxit['contactStore'].createGroup(group)
        self.dialog.destroy()
