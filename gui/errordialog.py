'''
Created on May 18, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk

from twisted.python import log
from twisted.internet import reactor

def on_response(dialog, response_id, shutdown):
    dialog.destroy()
    if shutdown:
        reactor.stop()

def errorDialog(message, shutdown=False):
    log.msg(message)
    dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_OK, flags=gtk.DIALOG_MODAL, message_format=message)
    dialog.connect('response', on_response, shutdown)
    dialog.show()
