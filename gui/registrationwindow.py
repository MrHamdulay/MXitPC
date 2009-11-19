'''
Created on May 17, 2009

@author: Yaseen
'''
import os.path

import pygtk
pygtk.require('2.0')
import gtk

from gui.errordialog import errorDialog
from gui.entrymask import MaskEntry
from protocol.commands import RegistrationMessage

class RegistrationWindow:
    def __init__(self, applicationSession):
        self.applicationSession = applicationSession
        
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glades', 'RegistrationWindow.glade'))
        
        self.dialog = self.builder.get_object('RegistrationDialog')
        
        self.dobEntry = MaskEntry()
        self.dobEntry.set_mask('%4d-%2d-%2d')
        self.dobEntry.set_text('yyyy-mm-dd')
        dobHBox = self.builder.get_object('dobHBox')
        dobHBox.pack_end(self.dobEntry, False, False, 0)
        self.dobEntry.show()
        
        self.dialog.connect('response', self.on_registerButton_activated)
        self.dialog.show()
        
    def on_registerButton_activated(self, *args):
        nickname = self.builder.get_object('nicknameEntry').get_text()
        pin = self.builder.get_object('pinEntry').get_text()
        dob = self.dobEntry.get_text()
        if self.builder.get_object('maleButton').get_active():
            gender = 'male'
        else:
            gender = 'female'
        location = self.builder.get_object('locationEntry').get_text()
        language = self.builder.get_object('languageEntry').get_text()
        
        if not nickname:
            errorDialog("Please enter a nickname")
            return
            
        try:
            int(pin)
            if len(str(pin)) <4:
                raise ValueError
        except ValueError:
            errorDialog("Password must be a number and more than 4 digits")
            return
        self.applicationSession['tempPassword'] = pin
        
        #Todo: use a regular expression to check whether in correct format
        if len(dob) < 10:
            errorDialog("Please enter your Date of Birth")
            return
            
        if not len(location):
            errorDialog("Please enter a location")
            return
            
        if not len(language):
            errorDialog("Please enter a language")
            return
        
        message = RegistrationMessage(pin, nickname, dob, gender, location, language, self.applicationSession)
        self.applicationSession['protocolInstance'].sendMsg(message)
        
        self.dialog.destroy()
