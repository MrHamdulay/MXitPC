import os.path
import gtk

from twisted.python import log
from gui.errordialog import errorDialog

class LoginWindow:
    def __init__(self, mxit):
        self.mxit = mxit

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'LoginWindow.glade'))

        numberEntry = self.builder.get_object('numberEntry')
        numberEntry.set_text(self.mxit.settings['loginname'])
        numberEntry.set_editable(False)

        dialog = self.builder.get_object('LoginDialog')
        dialog.connect('response', self.on_response)
        dialog.show()

        self.builder.connect_signals(self)

    def on_loginWindow_destroy(self, widget):
        widget.destroy()
        del self.mxit.windows['LoginWindow']

    def on_response(self, dialog, response_id, *args):
        #If we get a response other then login return
        if not response_id == 0:
            return

        passwordEntry = self.builder.get_object('passwordEntry')
        password = passwordEntry.get_text()

        self.mxit.settings['tempPassword'] = password
        #Validation
        try:
            int(password)
            if len(password)<4:
                log.msg('< 4')
                raise ValueError
        except ValueError:
            errorDialog('Password must be a number and more than 4 characters')
            return

        self.mxit.settings['autoLogin'] = self.builder.get_object('rememberButton').get_active()

        self.mxit.do_login(password)

        dialog.destroy()
