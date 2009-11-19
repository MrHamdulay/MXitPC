'''
Created on June 1, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk
import os.path

class VibesBox:
    def __init__(self, callback):
        self.callback = callback
        
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'VibesMenu.glade'))
        
        self.window = self.builder.get_object('VibesBox')
        
        for i in range(1, 10):
            self.builder.get_object('button%d' % i).connect('clicked', self.on_button_clicked, i)
            
    def show(self):
        self.window.show()
            
    def on_button_clicked(self, widget, vibe):
        self.callback(':@%d' % vibe)
        self.window.hide()
