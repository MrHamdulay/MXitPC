'''
Created on May 24, 2009

@author: Yaseen
'''

import pygtk
pygtk.require('2.0')
import gtk
import os.path

from twisted.internet import reactor

class SplashScreen:
    def __init__(self, splash, applicationSession):
        self.applicationSession = applicationSession
        self.image = splash[3]
        self.timeToShow = splash[1]
        
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'SplashDialog.glade'))
        
        pixbuf = gtk.gdk.PixbufLoader()
        pixbuf.write(self.image)
        pixbuf.close()
        
        splash = self.builder.get_object('splash')
        splash.set_from_pixbuf(pixbuf.get_pixbuf())
        splash.show()
        
        window = self.builder.get_object('SplashWindow')
        window.set_keep_above(True)
        window.show()
        
        print self.timeToShow
        reactor.callLater(self.timeToShow, self.destroyWindow, window)
        
    def destroyWindow(self, window):
        window.destroy()
