try:
    import winsound
    import threading
except ImportError:
    winsound = None
    import pygtk
    import gtk
    
    import pygst
    pygst.require('0.10')
    import gst
import os.path
from twisted.internet import reactor
    
class Sound:
    def __init__(self, applicationSession):
        self.applicationSession = applicationSession
        if winsound == None:
            self.player = gst.element_factory_make("playbin", "player")
            bus = self.player.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_message_gst)
            
            
    def message_received(self):
        try:
            if not self.applicationSession['settings']['newMessageAlert']:
                return
        except KeyError:
            pass
        self.play_sound(os.path.join('sounds', 'onNewMessage.wav'))
        
    def contact_online(self):
        try:
            if not self.applicationSession['settings']['contactOnlineAlert']:
                return
        except KeyError:
            pass
        self.play_sound(os.path.join('sounds', 'onContactOnline.wav'))        
        
    def invite_received(self):
        try:
            if not self.applicationSession['settings']['contactInviteAlert']:
                return
        except KeyError:
            pass
        self.play_sound(os.path.join('sounds', 'onContactInvite.wav'))
            
    def play_sound(self, uri):
        if winsound == None:
            self.player.set_property('uri', 'file://'+os.path.abspath(uri))
            self.player.set_state(gst.STATE_PLAYING)
        else:
            #Won't their be a problem of starting too many threads? :?
            threading.Thread(target=winsound.PlaySound, args=(uri, winsound.SND_FILENAME)).start()
            #reactor.deferToThread(winsound.PlaySound, uri,  winsound.SND_FILENAME)
        
    def on_message_gst(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			self.player.set_state(gst.STATE_NULL)
		elif t == gst.MESSAGE_ERROR:
			self.player.set_state(gst.STATE_NULL)
			print "Sound error", message.parse_error()
