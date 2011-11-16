import os.path
import gtk
from gtk.gdk import Pixbuf

from twisted.python import log
from twisted.internet import reactor

from protocol.constants import OFFLINE, ONLINE, AWAY, BUSY
from contact import Contact

from constants import *

class ContactModel(gtk.GenericTreeModel):
    #Contact list grouped according to groups
    _contactList = {'default': []}
    _groupList = []
    _columnTypes = (str, str, str, Pixbuf, int, int, Pixbuf)
    _columnNames = ('Nickname', 'Contact Address', 'Group', 'Presence', 'mood', 'type', 'Message available'),
    _contactContactList = {}

    def add(self, contactAddress, nickname, presence, mood, contactType, group=None):
        presence = int(presence)
        mood = int(presence)

        if self._groupList.count(group) == 0:
            self._groupList.append(group)
            #self._groupList.sort()
            self._contactList[group] = []
            try:
                path= (self._groupList.index(group),)
                self.row_inserted(path, self.get_iter(path))
            except ValueError:
                pass

        contact = Contact(contactAddress, nickname, group, presence, mood, contactType, False)
        self._contactList[group].append(contact)
        self._contactContactList[contactAddress] = contact

        path = (self._groupList.index(group), self._contactList[group].index(contact))
        self.row_inserted(path, self.get_iter(path))

    def getContact(self, contactAddress):
        return self._contactContactList[contactAddress] if contactAddress in self._contactContactList else None

    #def add(self, contactAddress, nickname, presence, mood, contactType, group=None):
    def update(self, contactAddress, nickname, group, presence, mood, contactType):
        ''' NB: Contact address has to stay the same '''
        if isinstance(contact, list):
            return

        for i, c in enumerate(self._contactList[contact.group]):
            if c.contactAddress == contact.contactAddress:
                self._contactList[contact.group][i] = contact
                path = (self._groupList.index(contact.group), self._contactList[contact.group].index(contact))
                self.row_changed(path, self.get_iter(path))
                return

        for c in self._contactList.itervalues():
            if c.contactAddress == contact.contactAddress:
                #TODO: Finish
                pass

    def remove(self, contact):
        self._contactList[contact.group].remove(contact)
        if self._contactList[contact.group].count() == 0:
            self._groupList.remove(contact.group)

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_column_type(self, n):
        return self._columnTypes[n]

    def on_get_n_columns(self):
        return len(self._columnTypes)

    def on_get_path(self, contact):
        return self._groupList.index(contact.group), self._contactList[contact.group].index(contact)

    def on_iter_next(self, contact):
        if isinstance(contact, list):
            try:
                return _groupList[_groupList.index(contact)+1]
            except IndexError:
                return None
        try:
            return _contactList[contact.group][_contactList[contact.group].index(contact)+1]
        except IndexError:
            try:
                return _contactList[_groupList[_groupList.index(contact.group)+1]][0]
            except IndexError:
                return None

    def on_get_iter(self, path):
        try:
            return self._contactList[self._groupList[path[0]]][path[1]]
        except IndexError:
            try:
                return self._groupList[path[0]]
            except IndexError:
                return None

    def on_iter_has_child(self, rowref):
        return isinstance(rowref, list)

    def on_iter_n_children(self, contact):
        return len(_contactList[contact.group])

    def on_iter_nth_child(self, rowref, n):
        try:
            return _contactList[rowref].index(n)
        except IndexError:
            return None

    def on_iter_parent(self, child):
        if isinstance(child, Contact):
            return child.group
        else:
            return None

    def on_get_value(self, contact, column):
        if isinstance(contact, list):
            return None

        if column == 0:
            return contact.nickname
        elif column == 1:
            return contact.contactAddress
        elif column == 2:
            return contact.group
        elif column == 3:
            return contact.presence
        elif column == 4:
            return contact.mood
        elif column == 5:
            return contact.contactType
        elif column == 6:
            return contact.messageAvailable

class ContactList:
    def __init__(self, treeview, mxit, contactList=None):
        self.mxit = mxit
        self.view = treeview

        self._initResources()
        self._initTree()

    def _initTree(self):
        self.treeModel = ContactModel()
        #Sort store according to presence
        self.friendListSortable = gtk.TreeModelSort(self.treeModel)
        self.friendListSortable.set_default_sort_func(self._treeSort)
        self.friendListSortable.set_sort_column_id(-1, gtk.SORT_ASCENDING)

        self.hideOffline = self.friendListSortable.filter_new()
        self.hideOffline.set_visible_func(self.hideOfflineFilterFunc)

        self.view.set_model(self.hideOffline)
        self.view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)
        self.view.set_headers_visible(False)

        textCellRenderer = gtk.CellRendererText()
        pixbufCellRenderer = gtk.CellRendererPixbuf()
        pixbufCellRenderer.set_property('xalign', 0.0)

        '''presenceColumn = gtk.TreeViewColumn('Presence', pixbufCellRenderer, pixbuf=3)
        self.view.append_column(presenceColumn)
        presenceColumn.pack_start(pixbufCellRenderer)'''

        nicknameColumn = gtk.TreeViewColumn('Nickname', textCellRenderer, text=0)
        nicknameColumn.set_max_width(170)
        self.view.append_column(nicknameColumn)
        nicknameColumn.pack_start(textCellRenderer)

        self.view.set_search_column(0)

        '''moodColumn = gtk.TreeViewColumn('Mood', pixbufCellRenderer, pixbuf=5)
        self.view.append_column(moodColumn)
        moodColumn.pack_start(pixbufCellRenderer)

        messageAvailableColumn = gtk.TreeViewColumn('MessageAvailable', pixbufCellRenderer, pixbuf = 7)
        self.view.append_column(messageAvailableColumn)
        messageAvailableColumn.pack_start(pixbufCellRenderer)'''

    def _initResources(self):
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

    def _treeSort(self, treemodel, iter1, iter2, user_data=None):
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
        return not iter.presence == 0

    def parseContactList(self, contactList):
        ''' Takes contact list from server and adds it to TreeStore '''
        for group, contactAddress, nickname, presence, contactType, mood in contactList:
            if group == '':
                group = None

            presence = int(presence)
            mood = int(mood)
            contactType = int(contactType)

            if self.treeModel.getContact(contactAddress) is None:
                self.treeModel.add(contactAddress, nickname, presence, mood, contactType, group)
            else:
                self._contactContactList[contactAddress].on_contactUpdate(nickname, group, presence, mood, self.mxit)
                self.updateRow(contactAddress, nickname, group, presence, mood, contactType)

        self.hideOffline.refilter()
