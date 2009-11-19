from threading import Thread
import gtk
import time

class AnimateImage(Thread):
    def __init__(self, widget, imagepath, dismissevent):
        Thread.__init__(self)
        self.daemon = 1
        self.widget = widget
        self.pixbufanimation = gtk.gdk.PixbufAnimation(imagepath)
        self.pixbufanimationiter = self.pixbufanimation.get_iter()
        self.dismissevent = dismissevent

    def run(self):
        self.widget.set_from_pixbuf(self.pixbufanimationiter.get_pixbuf())

        while not self.dismissevent.is_set():
            self.pixbufanimationiter.advance()
            self.widget.set_from_pixbuf(self.pixbufanimationiter.get_pixbuf())
            #time.sleep(self.pixbufanimationiter.get_delay_time()/1000)
            try:
                time.sleep(0.25)
            except:
                pass
