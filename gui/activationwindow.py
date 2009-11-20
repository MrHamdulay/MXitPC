import gtk
import os.path
import time

from gui.errordialog import errorDialog
from gui.loginwindow import LoginWindow
from gui.animation import AnimateImage
from protocol import challenge
from protocol.commands import RegistrationMessage

from threading import Event

class ActivationWindow:
    is_logging_in = True
    animationCancelEvent = Event()
    
    def __init__(self, mxit):
        self.mxit = mxit
        self.request_activation()

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join('gui', 'glade', 'ActivationWindowNew.glade'))

        self.header_image = gtk.gdk.pixbuf_new_from_file(os.path.join('gui', 'images', 'MXit_outlined_lifestyle_trans.png'))

        self.assistant = self.builder.get_object('ActivationAssistant')

        self.assistant.set_page_header_image(self.assistant.get_nth_page(0), self.header_image)
        image = self.builder.get_object('animationImage')
        AnimateImage(image, os.path.join('gui', 'images', 'loading.gif'), self.animationCancelEvent).start()


        cell = gtk.CellRendererText()
        self.builder.get_object('languageCombo').pack_start(cell, True)
        self.builder.get_object('languageCombo').add_attribute(cell, 'text', 1)
        self.builder.get_object('locationCombo').pack_start(cell, True)
        self.builder.get_object('locationCombo').add_attribute(cell, 'text', 1)

        
        self.assistant.show_all()
        #self.assistant.set_deletable(True)

        self.assistant.set_page_complete(self.assistant.get_nth_page(0), False)
        for i in range(1, 2):
            self.assistant.set_page_complete(self.assistant.get_nth_page(i), True)
        
        self.builder.connect_signals(self)

    def __del__(self):
        self.assistant.hide()
        self.assistant.destroy()

    def prepare_page(self, assistant, page, *args):
        self.assistant.set_page_header_image(page, self.header_image)
        if assistant.get_current_page() == 3:
            image = self.builder.get_object('loadingAnimation')
            AnimateImage(image, os.path.join('gui', 'images', 'loading.gif'), self.animationCancelEvent).start()
    
    def page_changed(self, assistant, *args):
        if assistant.get_current_page() == 2:
            self.animationCancelEvent.clear()
            self.is_logging_in = self.builder.get_object('loginButton').get_active()
            challenge_response = self.builder.get_object('captchaEntry').get_text()
            number = self.builder.get_object('numberEntry').get_text()
            language = self.builder.get_object('languageStore')[self.builder.get_object('languageCombo').get_active()][0]
            location = self.builder.get_object('locationStore')[self.builder.get_object('locationCombo').get_active()][0]

            self.challenge.challengeReply(self.received_challenge_reply_reply, challenge_response, number, self.is_logging_in, location, language) 
            if not self.builder.get_object('registerButton').get_active():
                assistant.set_current_page(3)
        elif assistant.get_current_page() == 3:
            nickname = self.builder.get_object('nicknameEntry').get_text()
            password = self.builder.get_object('passwordEntry').get_text()

            #Get date from calendar
            year, month, day = self.builder.get_object('dobCalendar').get_date()
            dob = time.strftime('%Y-%m-%d', (year, month+1, day, 1,0,0,0,0,0))
            gender = self.builder.get_object('maleButton').get_active() 
            language = self.builder.get_object('languageStore')[self.builder.get_object('languageCombo').get_active()][0]
            location = self.builder.get_object('locationStore')[self.builder.get_object('locationCombo').get_active()][1]
            self.register(nickname, password, dob, gender, location, language)

    def request_activation(self):
        self.challenge = challenge.Challenge(self.on_challenge_error)
        self.challenge.requestChallenge(self.on_received_activation_info)

    def on_challenge_error(self, error, *args):
        r = error.trap(challenge.CaptchaException, challenge.MXitServerException)
        if r == challenge.CaptchaException or r == challenge.MXitServerException:
            errorDialog(error.getErrorMessage())
            self.load_captcha(self.challenge.challengeData['captcha'])
            self.animationCancelEvent.set()
            self.assistant.set_current_page(1)

    def on_received_activation_info(self, challengeData):
        self.challengeData = challengeData
        self.animationCancelEvent.set()
        self.load_captcha(challengeData['captcha'])

        for locale, language_name in self.challengeData['languages']:
            self.builder.get_object('languageStore').append((locale, language_name))
        for country_code, country_name in self.challengeData['countries']:
            self.builder.get_object('locationStore').append((country_code, country_name))
        self.assistant.set_page_complete(self.assistant.get_nth_page(0), True)

    def received_challenge_reply_reply(self, challengeData):
        self.connectionInformation = challengeData
        self.mxit.settings.update(challengeData)
        self.animationCancelEvent.set()
        self.assistant.set_page_complete(self.assistant.get_nth_page(2), True)
        if challengeData['category'] == '1':
           self.assistant.set_current_page(4)

    def register(self, nickname, password, dob, gender, location, language):
        self.mxit['tempPassword'] = password
        self.mxit.initConnection()
        #Todo: validation
        message = RegistrationMessage(password, nickname, dob, gender, location, language, self.mxit)
        self.mxit.sendMsg(message)
        #self.assistant.set_deletable(True)
        
    def close_assistant(self, *args):
        #Only close window if we done with everything
        if self.assistant.get_current_page() <= 3:
            return
        self.assistant.hide()
        self.assistant.destroy()

        self.mxit.init_connection()
        LoginWindow(self.mxit)

    def load_captcha(self, captchaImageData):
        captchaImage = self.builder.get_object('captchaImage')

        pixbuf = gtk.gdk.PixbufLoader()
        pixbuf.write(captchaImageData)
        pixbuf.close()
        pixbuf = pixbuf.get_pixbuf()

        captchaImage.set_from_pixbuf(pixbuf)
        captchaImage.show()
