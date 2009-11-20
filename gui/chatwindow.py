'''
Created on May 14, 2009

@author: Yaseen
'''
import gtk
try:
    import gtkspell
except ImportError:
    #No windows build for gtkspell
    pass

import os.path
import time
import datetime
import re

from gui.htmltextview import HtmlTextView
from gui.smileywindow import SmileyWindow
from gui.vibeswindow import VibesBox
from protocol.commands import Message
from protocol.constants import * 

from constants import SMILEYS, PRESENCE_IMAGES_BASE_DIR, PRESENCE_IMAGES_FILENAMES
import markup

class ChatTab(gtk.ScrolledWindow):
    def __init__(self, contact, parent, mxit):
        gtk.ScrolledWindow.__init__(self)

        self.contact = contact
        self.parentWindow = parent
        self.mxit = mxit

        self.textview = HtmlTextView()
        self.textview.connect('focus-in-event', self.receivedFocus)
        self.textview.connect('url-clicked', self.urlClicked)
        self.textview.set_wrap_mode(gtk.WRAP_WORD)
        self.textview.show()
        self.add(self.textview)
        self.show()
        
        self._open = False
        
    def close_tab(self):
        self._open = False
        
    def open_tab(self):
        self._open = True
        
    def reopenTab(self, parentwindow):
        self.parentWindow = parentwindow
        self._open = True
        
    def isOpen(self):
        return self._open

    def urlClicked(self, textview, url, type):
        data = url.split('|')
        print data
        if data[0] == 'send':
            message = Message(self.contact.contactAddress, data[1])
            self.mxit.sendMsg(message)
            self.parseAndInsertMessage(0, time.time(), 1, 0, data[1])
        
    def _sanitiseMessage(self, message):
        #Unneeded for some reason
        return message.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;').replace('\n', '<br />\n')
        
    def _parseMessage(self, message):
        #Convert MXit markup to HTML for use in textview
        message = self._sanitiseMessage(message)
        for expression, file in SMILEYS.iteritems():
            tag = '<img src="file://%s" />' % (os.path.join('gui', 'images', 'chatemoti', file))
            message = re.sub(expression, tag, message)
        #Todo: custom emoticons
        return message

    def _insertHtml(self, html):
        try:
            self.textview.display_html(html)
        except Exception:
            #Probably caused by not well-formed html
            #print 'Bad html', html
            pass
        #self.scroll_to_iter(end_iter, 0.1, True, 0.0, 0.5)
        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.1)
    
    def parseAndInsertMessage(self, origin, contactAddress, timestamp, type, msg):
        ''' Parse message for emoticons and MXit markup 
        
        origin: 1 if from server, 0 if from us'''

        msg = markup.parse(msg)
        html = '<p>'
        if origin:
            html = '%s<span style="color: red">%s </span>' % (html, self._sanitiseMessage(self.contact.nickname))
            if datetime.date.today().day == datetime.datetime.fromtimestamp(timestamp).day:
                senttime = datetime.datetime.fromtimestamp(timestamp).time().strftime('%H:%M')
            else:
                senttime = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%y %H:%M')
            html = '%s<span style="color: grey">%s </span>' % (html, senttime)
        else:
            html = '%s<span style="color: blue">You: </span>' % html
            
        html += self._parseMessage(msg)
        html = '%s</p>' % (html)

        self._insertHtml(html)

    def contact_modified(self, modification, changed):
        if changed == 'presence':
            print 'presence changing'
            self._insertHtml('<span style="color: grey">%s is now %s</span>' % (self.contact.nickname, PRESENCE[modification]))
            self.parentWindow.notebook.set_tab_label(self, self.parentWindow.create_tab_label(True, self.contact))

        elif changed == 'mood':
            self._insertHtml('<span style="color: grey">%s is now %s</span>' % (self.contact.nickname, MOODS[modification]))

        
    def receiveMessage(self, contactAddress, timestamp, type, msg, id=0, flags=0):
        ''' Callback function for when we receive a message 
        
        data is a list containing all information sent from server'''
        
        self.parseAndInsertMessage(1, contactAddress, timestamp, type, msg)
        
        if not self.parentWindow.get_active_tab() == self:
            self.parentWindow.notebook.set_tab_label(self, self.parentWindow.create_tab_label(True, self.contact))
            self.mxit['contactStore'].updateRow(contactAddress, messageAvailable=1)
        else:
            self.mxit['contactStore'].updateRow(contactAddress, messageAvailable=0)
            
        self.mxit['sound'].message_received()
            
    def receivedFocus(self, window, *args):
        self.mxit['contactStore'].updateRow(self.contact.contactAddress, messageAvailable=0)

class MultiMxTab(ChatTab):
    def __init__(self, contact, parent, mxit):
        ChatTab.__init__(self, contact, parent, mxit)

    def parseAndInsertMessage(self, origin, contactAddress, timestamp, type, msg):
        print origin, contactAddress, type 
        nickname = self.contact.nickname
        if type == MESSAGE_TYPE_NORMAL:
            start = msg.find('<')
            if start == -1: return
            end = msg.find('>')
            nickname = msg[start+1:end]
            msg = msg[end+1:]

        #msg = markup.parse(msg)
        print 'wtf'
        html = '<p>'
        if origin:
            html += '<span style="color: red">%s </span>' % nickname
        else:
            html += '<span style="color: blue">You: </span>'
        html += self._parseMessage(msg)
        html += '</p>'

        self._insertHtml(html)

class ChatWindow:
    def __init__(self, mxit):
        self.mxit = mxit
        self.smileyWindow = None
        self.smileyList = []
        self.tabList = {}
        self.vibesBox = None
        
        self.initGui()
        self.window.show_all()

        self.initCallbacks()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'ChatWindow.glade'))
        self.window = self.builder.get_object('ChatWindow')
        self.builder.connect_signals(self)
        
        self.notebook = self.builder.get_object('ChatBoxNotebook')
        self.notebook.connect('switch-page', self.on_notebook_pageChanged)
        
        #Removed because it introduces too many bugs
        #gtk.notebook_set_window_creation_hook(self.windowCreate)

        try:
            self.spell = gtkspell.Spell(self.builder.get_object('entryView'))
        except:
            pass

    def on_contact_modified(self, modification, contact, changed):
        try:
            tab = self.tabList[contact.contactAddress] 
            tab.contact_modified(modification, changed)
        except KeyError:
            #When a key error is thrown its most likely becauseuser hasn't opened a tab for them yet
            pass

    def initCallbacks(self):
        self.mxit['contactCallback'].append(self.on_contact_modified)

    def get_active_tab(self):
        return self.notebook.get_nth_page(self.notebook.get_current_page())
            
    def create_tab_label(self, gotMessage, contact):
        box = gtk.HBox()
        if not gotMessage:
            label = gtk.Label(contact.nickname)
        else:
            label = gtk.Label()
            label.set_markup('<b><span color="grey" style="italic">%s</span></b>' % contact.nickname)

        presenceimage = gtk.image_new_from_file(os.path.join(PRESENCE_IMAGES_BASE_DIR, PRESENCE_IMAGES_FILENAMES[contact.presence]))
        closeimage = gtk.Image()
        closeimage.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        closebutton = gtk.Button()
        closebutton.set_image(closeimage)
        closebutton.set_relief(gtk.RELIEF_NONE)
        closebutton.connect('clicked', self.close_tab, contact)
        
        box.add(presenceimage)
        box.add(label)
        box.add(closebutton)
        box.show_all()
        return box
        
    def create_chat_tab(self, contact):
        label = self.create_tab_label(False, contact) 

        if self.tabList.has_key(contact.contactAddress):
            tab = self.tabList[contact.contactAddress]
        else:
            if contact.contactType == CONTACT_TYPE_MULTIMIX:
                self.tabList[contact.contactAddress] = tab = MultiMxTab(contact, self, self.mxit)
            else:
                self.tabList[contact.contactAddress] = tab = ChatTab(contact, self, self.mxit)
            contact.set_chat_tab(tab)
            
        if tab.isOpen():
            return
            
        self.notebook.append_page(tab)
        self.notebook.set_tab_reorderable(tab, True)
        self.notebook.set_tab_label(tab, label) 
        
        tab.open_tab()
        #Make sure this window is showing
        self.window.show_all()
        
    def close_tab(self, button, contact):
        tab = self.tabList[contact.contactAddress]
        tab.close_tab()
        self.notebook.remove_page(self.notebook.page_num(tab))
        
        numPages = self.notebook.get_n_pages()
        if numPages == 0:
            self.window.hide()
            return

    def on_text_inserted(self, textview, string, *args):
        print 'on_text_inserted'
        if '\n' in string:
            buffer = textview.get_buffer()
            buffer.delete(buffer.get_iter_at_offset(-1), buffer.get_end_iter())
            
    def on_smileyButton_clicked(self, *args):
        if self.smileyWindow == None:
            self.smileyWindow = SmileyWindow(self.addSmiley)
        self.smileyWindow.show()
        
    def on_vibesButton_clicked(self, *args):
        if self.vibesBox == None:
            self.vibesBox = VibesBox(self.appendToEntry)
        self.vibesBox.show()
    
    def addSmiley(self, pixbuf, smiley_code):
        buf = self.builder.get_object('entryView').get_buffer()
        iter = buf.get_end_iter()
        buf.insert_pixbuf(iter, pixbuf)
        self.smileyList.append((iter, smiley_code))
            
    def appendToEntry(self, addition):
        buf = self.builder.get_object('entryView').get_buffer()
        buf.insert(buf.get_end_iter(), addition)
        
    def on_keypress(self, widget, event, *args):
        #We are only looking for enter button presses
        #Todo: Replace 65293 with actual constant
        if not event.keyval == 65293:
            return
            
        buf = self.builder.get_object('entryView').get_buffer()
        for iter, smiley_code in self.smileyList:
            buf.insert(iter, smiley_code)
        msg = buf.get_text(buf.get_start_iter(),buf.get_end_iter())
        buf.set_text('')
        
        #Get contactAddress of active tab
        contactAddress = self.get_active_tab().contact.contactAddress
        
        message = Message(contactAddress, msg)
        self.mxit.sendMsg(message)
        
        self.get_active_tab().parseAndInsertMessage(0, time.time(), 1, 0, msg)
        
        return False
        
    def on_notebook_pageChanged(self, notebook, page, page_num, userdata=None):
        tab = notebook.get_nth_page(page_num)
        self.window.set_title(tab.contact.nickname)
        notebook.set_tab_label(tab, self.create_tab_label(False, tab.contact))
    
    def on_closeWindow_activate(self, *args):
        #Had to create this function to ensure window's widgets never get destroyed
        self.window.hide()
        return True
