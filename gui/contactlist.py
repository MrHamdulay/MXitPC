import os.path
import gtk

from twisted.python import log
from twisted.internet import reactor

from protocol.constants import OFFLINE, ONLINE, AWAY, BUSY
from contact import Contact

from constants import *

class ContactList:
    _rowCacheIter = {}
    def __init__(self, treeview, mxit, contactList=None):
        self.mxit = mxit
        
        self.view = treeview
        self.friendListNames = []
        self.groupList = {}
        self.contactContactList = {}
        
        self.initResources()
        self.initTree()
        
    def _getRow(self,  model, path, iterRow, contactAddress=None):
        if model[path][1] == contactAddress:
            #Urgh...completely disgusting hack
            self._tempRow = model[path]
        
    def getRow(self, contactAddress):
        ''' Get row that corresponds to this contactAddress '''
        #Todo: remember to remove cache when we update row
        if self._rowCacheIter.has_key(contactAddress):
            self.friendListModel
        #Very inefficient
        self.friendListModel.foreach(self._getRow, contactAddress)
        return self._tempRow
        
    def getContact(self, contactAddress):
        return self.contactContactList[contactAddress]
    
    def initTree(self):
        ''' The store should contain the following:
            nickname
            contactAddress
            group
            presence
            presence_int #Used for sorting purposes
            mood
            type
            messageAvailable'''
        self.friendListModel = gtk.TreeStore(str, str, str, gtk.gdk.Pixbuf, int, gtk.gdk.Pixbuf, int, gtk.gdk.Pixbuf)
        #Sort store according to presence
        self.friendListSortable = gtk.TreeModelSort(self.friendListModel)
        self.friendListSortable.set_default_sort_func(self.treeSort)
        self.friendListSortable.set_sort_column_id(-1, gtk.SORT_ASCENDING)
        
        self.hideOffline = self.friendListSortable.filter_new()
        self.hideOffline.set_visible_func(self.hideOfflineFilterFunc)
        
        self.view.set_model(self.hideOffline)
        self.view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)
        self.view.set_headers_visible(False)
        
        textCellRenderer = gtk.CellRendererText()
        pixbufCellRenderer = gtk.CellRendererPixbuf()
        pixbufCellRenderer.set_property('xalign', 0.0)
        
        presenceColumn = gtk.TreeViewColumn('Presence', pixbufCellRenderer, pixbuf=3)
        self.view.append_column(presenceColumn)
        presenceColumn.pack_start(pixbufCellRenderer)
        
        nicknameColumn = gtk.TreeViewColumn('Nickname', textCellRenderer, text=0)
        nicknameColumn.set_max_width(170)
        self.view.append_column(nicknameColumn)
        nicknameColumn.pack_start(textCellRenderer)
        
        self.view.set_search_column(0)
        
        moodColumn = gtk.TreeViewColumn('Mood', pixbufCellRenderer, pixbuf=5)
        self.view.append_column(moodColumn)
        moodColumn.pack_start(pixbufCellRenderer)
        
        messageAvailableColumn = gtk.TreeViewColumn('MessageAvailable', pixbufCellRenderer, pixbuf = 7)
        self.view.append_column(messageAvailableColumn)
        messageAvailableColumn.pack_start(pixbufCellRenderer)
        
    def initResources(self):
        self.presencePixbufs = []
        for presenceFilename in PRESENCE_IMAGES_FILENAMES:
            if not presenceFilename == None:
                self.presencePixbufs.append(gtk.gdk.pixbuf_new_from_file(os.path.join(PRESENCE_IMAGES_BASE_DIR, presenceFilename)))
            else:
                self.presencePixbufs.append(None)
        
        self.moodPixbufs = [gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 1, 1),]
        for moodFilename in EMOTICONS_IMAGES_FILENAMES:
            self.moodPixbufs.append(gtk.gdk.pixbuf_new_from_file(os.path.join(EMOTICONS_IMAGES_BASE_DIR, moodFilename)))
            
        base = os.path.join('gui', 'images')
        self.messagesAvailable = [gtk.gdk.pixbuf_new_from_file(os.path.join(base, 'Mail.png')),
                                  gtk.gdk.pixbuf_new_from_file(os.path.join(base, 'Unread_Mail.png')),]  
            
    def treeSort(self, treemodel, iter1, iter2, user_data=None):
        sort = 0
        
        presence1 = treemodel.get_value(iter1, 4)
        presence2 = treemodel.get_value(iter2, 4)
        nickname1 = treemodel.get_value(iter1, 0)
        nickname2 = treemodel.get_value(iter2, 0)
        contactaddress1 = treemodel.get_value(iter1, 1)
        contactaddress2 = treemodel.get_value(iter2, 1)
        
        if presence1 == OFFLINE and not presence2 == OFFLINE:
            sort = 1
        elif not presence1 == OFFLINE and presence2 == OFFLINE:
            sort = -1
        elif not presence1 == OFFLINE and not presence2 == OFFLINE:
            if nickname1 == 'Info':
                return -1
            elif nickname2 == 'Info':
                return 1
            
            if contactaddress1.endswith('@group') and not contactaddress2.endswith('@group'):
                return 1
            elif not contactaddress1.endswith('@group') and contactaddress2.endswith('@group'):
                return -1
            
            try:
                for i in xrange(len(nickname1)):
                    if ord(nickname1[i]) < ord(nickname2[i]):
                        sort = -1
                        break
                    elif ord(nickname1[i]) > ord(nickname2[i]):
                        sort = 1
                        break
            except IndexError:
                pass
                
        return sort
        
    def hideOfflineFilterFunc(self, model, iter, user_data=None):
        ''' Returns value that specifies whether user should be visible. Used by hide offline filter '''
        return not model.get_value(iter, 4) == 0

    def updateRow(self, contactAddress, nickname=None, group=None, presence=None, mood=None, contactType=None, messageAvailable=None):
        row = self.getRow(contactAddress)
        if not nickname == None:
            row[0] = nickname
        if not group == None:
            row[2] = group
        if not presence == None:
            row[3] = self.presencePixbufs[presence]
            #Move to callback for contact
            if row[4] == OFFLINE and not presence == OFFLINE:
                reactor.callLater(0, self.mxit['sound'].contact_online)
            row[4] = presence
        if not mood == None:
            row[5] = self.moodPixbufs[mood]
        if not contactType == None:
            row[6] = contactType
        if not messageAvailable == None:
            row[7] = self.messagesAvailable[messageAvailable]
        
    def createGroup(self, groupName):
        ''' Create a group with groupName only if group doesn't exist
        
        Note: only updates the server if a user is created that uses the group '''
        if self.groupList.has_key(groupName) == 0:
            groupIter = self.friendListModel.append(None, (groupName, '%s@group'%groupName, '', None, 1, None, 0, None))
            self.groupList[groupName] = gtk.TreeRowReference(self.friendListModel, self.friendListModel.get_path(groupIter))
            
    def newContact(self, contactAddress, group, nickname, presence, mood, contactType):
        contact = self.contactContactList[contactAddress] = Contact(contactAddress, nickname, group, presence, mood, contactType, False)
    
        groupIter = None
        if not group == None:
            groupIter = self.friendListModel.get_iter(self.groupList[group].get_path())

        self.friendListModel.append(groupIter, (nickname, contactAddress, group,
                                    self.presencePixbufs[presence], presence,
                                    self.moodPixbufs[mood], 
                                    contactType, None))
        self.friendListNames.append(contactAddress)
        
    def parseContactList(self, contactList):
        ''' Takes contact list from server and adds it to TreeStore '''
        #Very inefficient
        for group, contactAddress, nickname, presence, contactType, mood in contactList:
            if group == '':
                group = None
                
            presence = int(presence)
            mood = int(mood)
            contactType = int(contactType)
            
            if self.groupList.has_key(group) == 0 and not group == None:
                self.createGroup(group)

            if not self.friendListNames.count(contactAddress):
                self.newContact(contactAddress, group, nickname, presence, mood, contactType)
            else:
                self.contactContactList[contactAddress].on_contactUpdate(nickname, group, presence, mood, self.mxit)
                self.updateRow(contactAddress, nickname, group, presence, mood, contactType)
                
        self.hideOffline.refilter()
