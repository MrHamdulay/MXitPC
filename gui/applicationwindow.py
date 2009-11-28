import gtk
import os.path
import urlparse
import shelve

from twisted.internet import reactor
from twisted.python import log

from gui.contactlist import ContactList
from gui.chatwindow import ChatWindow
from gui.editcontactdialog import EditContactDialog
from gui.addgroupdialog import AddGroupDialog
from gui.errordialog import errorDialog
from gui.splashscreen import SplashScreen
from gui.preferencesdialog import PreferencesDialog
from gui.activationwindow import ActivationWindow
from gui.multimxcreatewindow import MultiMXCreateWindow

from protocol.commands import SetMoodMessage, SetPresenceMessage
from protocol.constants import *

from constants import *

#Todo: move a lot of stuff out of here

class ApplicationWindow:
    connected = False
    status = ''
    presence = 1

    def __init__(self, session):
        self.mxit = session
        
        #Set default window icon
        gtk.window_set_default_icon_from_file(os.path.join('gui', 'images', 'desktop.ico'))
        
        SplashScreen()
        self.initGui()

    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'MainWindow.glade'))
        
        self.window = self.builder.get_object('MainWindow')        
        self.window.show()
        
        try:
            self.status = self.mxit.settings['status'] 
            self.builder.get_object('statusEntry').set_text(self.status)
        except KeyError: 
            self.builder.get_object('statusEntry').set_text('Click here to change your status')

        self.builder.get_object('presenceItem').set_image(gtk.image_new_from_file(os.path.join('gui', 'images', 'presence', '1.png')))
        
        self.mxit.contactStore = ContactList(self.builder.get_object('ContactListTreeView'), self.mxit)
        
        self.builder.connect_signals(self)
        self.initMenuIcons()

        try:
            if not self.mxit.settings.has_key('rememberMood') or self.mxit.settings['rememberMood']:
                self.mood = self.mxit.settings['lastmood']
                if not int(self.mood) == 0:
                    mood = MOODS[self.mood]
                    message = SetMoodMessage(int(self.mood), self.mxit)
                    self.mxit.sendMsg(message)
                    self.builder.get_object('moodItem').set_image(gtk.image_new_from_file(os.path.join(MOOD_IMAGES_BASE_DIR, '%s.png' % mood)))
        except KeyError:
            #We ain't got no mood
            pass
            
    def initMenuIcons(self):
        for item in ['happy', 'sad', 'excited', 'invincible', 'hot', 
                     'angry', 'grumpy', 'sick', 'inlove', 'sleepy']:
            self.builder.get_object('%sItem' % item).set_image(gtk.image_new_from_file(os.path.join(MOOD_IMAGES_BASE_DIR, '%s.png' % item)))
            
        for item in ['online', 'away', 'busy']:
            self.builder.get_object('%sItem' % item).set_image(gtk.image_new_from_file(os.path.join(PRESENCE_IMAGES_BASE_DIR, '%s.png' % item)))

        self.builder.get_object('moodItem').set_image(gtk.image_new_from_file(os.path.join(MOOD_IMAGES_BASE_DIR, 'none.png')))

    def status_changed(self, widget, *args):
        self.status = widget.get_text()
        message = SetPresenceMessage(self.presence, self.status, self.mxit)
        self.mxit.sendMsg(message)
        self.mxit.settings['status'] = self.status
        print 'Status updated'
        
    def status_clicked(self, widget, *args):
        widget.select_region(0, -1)

    def setStatusLabel(self, status):
        self.builder.get_object('statusLabel').set_text(status)
                
    def on_hideOfflineItem_toggled(self, widget, *args):
        if widget.get_active():
            self.mxit['contactStore'].view.set_model(self.mxit['contactStore'].hideOffline)
        else:
            self.mxit['contactStore'].view.set_model(self.mxit['contactStore'].friendListSortable)
    
    def on_addContactItem_activate(self, widget):
        from gui.adduserwindow import AddUserWindow
        AddUserWindow(self.mxit)
    
    def on_multiMXItem_activate(self, widget):
        MultiMXCreateWindow(self.mxit)
        
    def on_preferencesItem_activate(self, widget):
        PreferencesDialog(self.mxit)
    
    def on_loginItem_activate(self, widget):
        self.mxit.windows['LoginWindow'] = LoginWindow(self.mxit)
        
    def on_registerItem_activate(self, widget):
        self.mxit.windows['RegistrationWindow'] = RegistrationWindow(self.mxit)
        
    def openChatTab(self, contactAddress):
        try:
            self.mxit.activeChatWindow.create_chat_tab(self.mxit.contactStore.getContact(contactAddress))
        except AttributeError:
            self.mxit.activeChatWindow = ChatWindow(self.mxit)
              
        self.mxit.activeChatWindow.create_chat_tab(self.mxit.contactStore.getContact(contactAddress))
        return self.mxit.activeChatWindow.tabList[contactAddress]
        
    def on_ContactListTreeView_row_activated(self, treeView, path, viewcolumn, userData = None):
        ''' Called when user double-clicks on friend in friend list '''
        model = treeView.get_model()
        iter = model.get_iter(path)
        #Retrieve contactAddress which is at column 1
        contactAddress = model.get_value(iter, 1)
        #If a group is selected then return
        if contactAddress.endswith('@group'):
            return
        tab = self.openChatTab(contactAddress)
        tab.parentWindow.notebook.set_current_page(tab.parentWindow.notebook.page_num(tab))

    def on_removeContactItem_activate(self, widget):
        from protocol.commands import RemoveContactMessage
        model, iterRow = self.mxit.contactStore.view.get_selection().get_selected()
        if not iterRow:
            errorDialog('Please select a contact first')
            return
        if model[iterRow][6] == CONTACT_TYPE_INFO or model[iterRow][6] == CONTACT_TYPE_GALLERY:
            errorDialog('Can\'t delete this contact')
            return
        message = RemoveContactMessage(model[iterRow][1])
        self.mxit.sendMsg(message)
        del model[iterRow]
        
    def on_editContactItem_activate(self, widget):
        model, iterRow = self.mxit.contactStore.view.get_selection().get_selected()
        if not iterRow:
            errorDialog('Please select a contact first')
            
        row = model[iterRow]
        
        EditContactDialog(row[1], row[0], self.mxit)
        
    def on_newGroupItem_activate(self, widget):
        AddGroupDialog(self.mxit)
    
    def on_MainWindow_destroy(self, widget):
        widget.destroy()
        self.mxit.do_logout()
            
    def on_mood_changed(self, menuitem, *args):
        mood = MOODS.index(menuitem.get_name()[:-4])
        self.mxit.settings['lastmood'] = mood
        self.builder.get_object('moodItem').set_image(gtk.image_new_from_file(os.path.join(MOOD_IMAGES_BASE_DIR, '%s.png' % menuitem.get_name()[:-4])))
        message = SetMoodMessage(int(mood), self.mxit)
        self.mxit.sendMsg(message)
      
    def on_presence_changed(self, menuitem, *args):
        #Found weird bug in glade that doesn't pass user data you put in the interface
        if menuitem.get_name() == 'onlineItem': presence = 1
        elif menuitem.get_name() == 'awayItem': presence = 2
        elif menuitem.get_name() == 'busyItem': presence = 4

        self.builder.get_object('presenceItem').set_image(gtk.image_new_from_file(os.path.join('gui', 'images', 'presence', '%d.png'%presence)))
        #Todo: as from protocol version 5.9.0 there is an option for status
        self.presence = presence
        message = SetPresenceMessage(presence, self.status, self.mxit)
        self.mxit.sendMsg(message)
    
    def on_presenceChange_activate(self, menuitem, presence, status):
        message = SetPresenceMessage(presence, status, self.mxit)
        self.mxit.sendMsg(message)
        
