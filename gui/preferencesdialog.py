'''
Created on May 31, 2009

@author: Yaseen
'''
import gtk
import os.path

from protocol.commands import GetProfileMessage, UpdateProfileMessage
from gui.entrymask import MaskEntry

from twisted.internet import reactor

class PreferencesDialog:
    _loadingProfile = False
    _profileLoaded = False
    def __init__(self, mxit):
        self.mxit = mxit
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'PreferencesDialog.glade'))
        
        dialog = self.builder.get_object('PreferencesDialog')
        dialog.connect('response', self.on_response)
        self.builder.get_object('notebook').connect('switch-page', self.on_notebook_switch_page)
        dialog.show()
        
        self.genderComboBox = gtk.combo_box_new_text()
        self.genderComboBox.append_text("Female")
        self.genderComboBox.append_text("Male")
        self.genderComboBox.show()
        self.builder.get_object('genderBox').pack_end(self.genderComboBox, False, False)
        
        self.dobEntry = MaskEntry()
        self.dobEntry.set_mask('%4d-%2d-%2d')
        self.dobEntry.show()
        self.builder.get_object('dobBox').pack_end(self.dobEntry, False, False)
        
        try:
            self.builder.get_object('autoLoginButton').set_active(self.mxit['settings']['autoLogin'])
            self.builder.get_object('contactInviteAlertButton').set_active(self.mxit['settings']['contactInviteAlert'])
            self.builder.get_object('contactOnlineAlertButton').set_active(self.mxit['settings']['contactOnlineAlert'])
            self.builder.get_object('messageAlertButton').set_active(self.mxit['settings']['newMessageAlert'])
            self.builder.get_object('rememberMoodButton').set_active(self.mxit['settings']['rememberMood'])
        except KeyError:
            self.builder.get_object('contactInviteAlertButton').set_active(True)
            self.builder.get_object('contactOnlineAlertButton').set_active(True)
            self.builder.get_object('messageAlertButton').set_active(True)
            self.builder.get_object('autoLoginButton').set_active(True)
            self.builder.get_object('rememberMoodButton').set_active(True)
            
    def on_notebook_switch_page(self, notebook, dont_use, page, *args):
        if page == 0 or self._loadingProfile:
            return
        self.mxit['get_profile_callback'] = self.get_profile_callback
        message = GetProfileMessage()
        self.mxit.sendMsg(message)
        
    def get_profile_callback(self, message):
        self.builder.get_object('loadingLabel').set_property('visible', False)
        self.builder.get_object('profileBox').set_property('visible', True)
        
        self.genderComboBox.set_active(int(message[0][3]))
        self.dobEntry.set_text(message[0][2])
        
        self.builder.get_object('nicknameEntry').set_text(message[0][0])
        self.builder.get_object('numberEntry').set_text(self.mxit['settings']['loginname'])
        self.builder.get_object('passwordEntry').set_text(self.mxit['settings']['password'])
        if message[0][1] == '1':
            self.builder.get_object('hideNumberButton').set_active(True)
        self._profileLoaded = True
        
    def on_response(self, dialog, response_id, *args):
        dialog.destroy()
        
        self.mxit['settings']['contactInviteAlert'] = self.builder.get_object('contactInviteAlertButton').get_active()
        self.mxit['settings']['contactOnlineAlert'] = self.builder.get_object('contactOnlineAlertButton').get_active()
        self.mxit['settings']['newMessageAlert'] = self.builder.get_object('messageAlertButton').get_active()
        self.mxit['settings']['autoLogin'] = self.builder.get_object('autoLoginButton').get_active()
        self.mxit['settings']['rememberMood'] = self.builder.get_object('rememberMoodButton').get_active()
        
        if self._profileLoaded:
            nickname = self.builder.get_object('nicknameEntry').get_text()
            password = self.builder.get_object('passwordEntry').get_text()
            dob = self.dobEntry.get_text()
            hideMobileNumber = self.builder.get_object('hideNumberButton').get_active()
            if self.genderComboBox.get_active() == 1:
                gender = 'm'
            else:
                gender = 'f'
            message = UpdateProfileMessage(password, nickname, hideMobileNumber, dob, gender, self.mxit)
            self.mxit.sendMsg(message)
