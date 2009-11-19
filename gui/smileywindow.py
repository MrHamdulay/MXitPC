'''
Created on June 1, 2009

@author: Yaseen
'''
import pygtk
pygtk.require('2.0')
import gtk
import os.path

smiley_dir = os.path.join('gui', 'images', 'chatemoti')
SMILEYS = {':)': 'smile.png',
           ':(': 'sad_smile.png',
           ';)': 'cool_smile.png',
           ':D': 'excited_smile.png',
           ':|': 'shocked_smile.png',
           ':O': 'surprised_smile.png',
           ':P': 'smile_with_tongue_out.png',
           ':$': 'embarrassed_smile.png',
           '8-)': 'cool_smile.png',
           '(H)': 'heart.png',
           '(F)': 'flower.png',
           '(m)': 'male.png',
           '(f)': 'female.png',
           '(*)': 'star.png',
           '(c)': 'chilli.png',
           '(x)': 'kiss.png',
           '(i)': 'idea.png',
           ':e': 'angry.png',
           ':x': 'censored.png',
           '(z)': 'bad_day.png',
           '(U)': 'coffee.png',
           '(G)': 'mr_green.png',
           ':o(': 'throwup_smiley.png',
           ':{': 'totally_surprised.png',
           ':}': 'in_love.png',
           '8o': 'rolling_eyes.png',
           ':\'(': 'crying.png',
           ':?': 'thinking.png',
           ':~': 'drooling.png',
           ':z': 'sleepy.png',
           ':L)': 'liar.png',
           '8|': 'nerdy.png',
           'P)': 'pirate.png'
           }

class SmileyWindow:
    def __init__(self, smileyCallback):
        self.callback = smileyCallback
        self.initGui()
        
    def initGui(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'SmileyWindow.glade'))
        
        self.window = self.builder.get_object('SmileyWindow')
        
        i = 1
        for smile in SMILEYS:
            image = self.builder.get_object('image%d' % i)
            image.set_from_file(os.path.join('gui', 'images', 'chatemoti', SMILEYS[smile]))
            button = self.builder.get_object('button%d' % i)
            button.connect('clicked', self.on_button_clicked, (image.get_pixbuf(), smile))
            i += 1
            
        self.window.show()
        
    def show(self):
        self.window.show()
            
    def on_button_clicked(self, widget, (pixbuf, smiley_code)):
        self.callback(pixbuf, smiley_code)
        self.window.hide()
