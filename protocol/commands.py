'''
Created on May 2, 2009

@author: Yaseen
'''
import gobject

from twisted.internet import reactor
from twisted.python import log

from protocol.pin import Pin
from protocol import constants
from protocol import chunk

from gui.errordialog import errorDialog

def handle_default(command, errorCode, errorMessage, message, mxit):
    ''' Default handler.

    Used for commands that have a simple acknowledgement reply.
    e.g. Keepalive command (1000)'''
    if errorCode:
        log.msg('Got error code %d with command %d' % (errorCode, command))
        log.msg('Error message: %s' % errorMessage)

class ClientMessage:
    ''' Superclass of all messages to the MXit server'''
    message = None
    command = None

    _sent = False

    def __init__(self, command, message=''):
        self.command = command
        self.message = message

    def getMessage(self):
        ''' Returns tuple containing cm and ms respectively '''
        return (self.command, self.message)

    def isSent(self):
        return self._sent

    def messageSent(self):
        self._sent = True

class LoginMessage(ClientMessage):
    ''' Sends a login message '''
    def __init__(self, password, locale, mxit):
        self.command = 1
        settings = mxit.settings
        distcode = settings['pid'][2:-8]

        password = Pin(password, settings['pid'])
        self.message =  [password, constants.VERSION, constants.GET_CONTACTS,
                         constants.CAPABILITIES, distcode, constants.FEATURES, settings['dial'], locale]

def handle_login(errorCode, errorMessage, message, mxit):
    ''' Function that handles servers login reply  '''
    if not errorCode == 0:
        return
    #Make sure that on next login we get a login screen and not the registration screen
    mxit.settings['registered'] = '1'
    #Temporary store password to be used for auto login
    mxit.settings['password'] = mxit.settings['tempPassword']

    sesid = message[0]
    message = message[1]

    gobject.timeout_add(0, mxit.MainWindow.setStatusLabel, 'Online')
    mxit.loggedIn = True
    if mxit.windows.has_key('LoginWindow'):
        gobject.timeout_add(0, mxit.windows['LoginWindow'].window.destroy)
    #Used when we need to reconnect
    mxit.settings['connectionProxy'] = message[3]
    mxit.settings['pricePlan'] = message[5]

    #Todo: Find the sweet spot for this and put it in the settings file
    reactor.callLater(120, mxit.do_keepalive)

class LogoutMessage(ClientMessage):
    ''' Logs user out '''
    def __init__(self, mxit):
        self.command = 2
        self.message = '0'

def handle_logout(*argse):
    log.msg('Received logout confirmation. Shutdown')
    reactor.stop()

class RequestContactsMessage(ClientMessage):
    def __init__(self):
        self.command = 3

def handle_get_contacts(errorCode, errorMessage, message, mxit,):
    gobject.timeout_add(0, mxit.contactStore.parseContactList, message)

class UpdateContactInfoMessage(ClientMessage):
    #Todo: finish
    def __init__(self, contactAddress, nickname, group):
        self.command = 5
        self.message = [group, contactAddress, nickname]

class InviteMessage(ClientMessage):
    ''' Invites a user '''
    def __init__(self, contactAddress, nickname, inviteMessage, group='', typeOf=0):
        self.command = 6
        self.message = [group, contactAddress, nickname, typeOf, inviteMessage]

def handle_invite_contact(errorCode, errorMessage, message, mxit):
    if not errorCode == 0:
        errorDialog(errorMessage+' Try using country code (e.g. 27) instead of 0 in the cellphone number')

class RemoveContactMessage(ClientMessage):
    ''' Remove (delete) a contact '''
    def __init__(self, contactAddress):
        self.command = 8
        self.message = [contactAddress]

def handle_receive_messages(errorCode, errorMessage, data, mxit):
    def received_message(contactAddress, timestamp, type, msg, id, flags):
        chatTab = mxit.MainWindow.openChatTab(contactAddress)
        chatTab.receiveMessage(contactAddress, timestamp, type, msg, id, flags)

    contactAddress = data[0][0]
    timestamp = int(data[0][1])
    type = int(data[0][2])

    print 'Received message of type',type

    try:
        id = int(data[0][3])
        flags = int(dat[0][4])
    except ValueError:
        id = 0
        flags = 0

    try:
        msg = data[1]
    except IndexError:
        #When user sends blank message this excepts
        msg = ''

    gobject.timeout_add(0, received_message, contactAddress, timestamp, type, msg, id, flags)

class Message(ClientMessage):
    ''' Sends a message to a contact '''
    def __init__(self, contactAddress, msg, type=1, flags=0):
        self.command = 10
        self.message = [contactAddress, msg, type, flags]

class RegistrationMessage(ClientMessage):
    ''' Registers user'''
    def __init__(self, password, nickname, dob, gender, location, language, mxit):
        self.command = 11
        distcode = mxit.settings['pid'][2:-8]
        password = Pin(password, mxit.settings['pid'])
        if gender == 'male' or gender:
            gender = 1
        else:
            gender = 0

        self.message = [password, constants.VERSION, constants.MAX_REPLY_LEN, nickname,
                        dob, gender, location, constants.CAPABILITIES, distcode,
                         constants.FEATURES, mxit.settings['dial'],
                         language]

def handle_register(errorCode, errorMessage, message, mxit):
    if not errorCode == 0:
        #Handle error
        print errorMessage
        return
    mxit.settings['registered'] = True
    mxit.settings['category'] = '1'
    mxit.settings['password'] = mxit.tempPassword

    gobject.timeout_add(0, mxit.MainWindow.setStatusLabel, 'Logged in')
    mxit.settings['connectionProxy'] = message[1][3]
    mxit.settings['pricePlan'] = message[1][3]
    mxit.settings['flags'] = message[1][6]
    mxit.settings['hiddenLoginname'] = message[2]

    gobject.timeout_add(0, mxitActivationWindow.__del__)
    #del mxit.ActivationWindow

    gobject.timeout_add(240*1000, mxit.do_keepalive)

class UpdateProfileMessage(ClientMessage):
    def __init__(self, password, name, hideLoginName, dob, gender, mxit):
        self.command = 12
        mxit.tempPassword = password
        password = Pin(password, mxit.settings['pid'])
        if hideLoginName:
            hideLoginName = '1'
        else:
            hideLoginName = '0'
        if isinstance(gender, str):
            if gender[0].lower() == 'm':
                gender = '1'
            else:
                gender = '0'
        self.message = [password, name, hideLoginName, dob, gender, '']

def handle_update_profile(errorCode, errorMessage, message, mxit):
    try:
        #Remember to change the password in settings only once we get this confirmation
        mxit.settings['password'] = mxit.tempPassword
    except KeyError:
        #For some reason this happens... find out why
        pass

class RequestMessagesMessage(ClientMessage):
    ''' Requests new messages from MXit Server '''
    def __init__(self):
        self.command = 9

def handle_get_multimedia_message(errorCode, errorMessage, message, mxit):
    chunk.parseChunk(message, mxit)

class GetProfileMessage(ClientMessage):
    ''' Retrieves user profile '''
    def __init__(self):
        self.command= 26

def handle_get_profile(errorCode, errorMessage, message, mxit):
    if not errorCode == 0:
        pass
    gobject.timeout_add(0, mxit.get_profile_callback, message)

class SetPresenceMessage(ClientMessage):
    ''' Sets user presence and status '''
    def __init__(self, presence, status, mxit):
        self.command = 32
        self.message = [int(presence), status]

class BlockInviteMessage(ClientMessage):
    ''' Block user from being able to invite again '''
    def __init__(self, contactAddress):
        self.command = 33
        self.message = [contactAddress]

class SetMoodMessage(ClientMessage):
    ''' Sets user mood '''
    def __init__(self, mood, mxit):
        self.command = 41
        self.message = [int(mood)]

class CreateMultiMX(ClientMessage):
    ''' Creates a temporary group chat
    aka MultiMx '''
    def __init__(self, groupname, contactlist):
        self.command = 44
        self.message = [groupname, len(contactlist)] + [contact.contactAddress for contact in contactlist]

def handle_create_multimix(errorCode, errorMessage, message, mxit):
    pass

invitationWindows = {}
def handle_got_invite(errorCode, errorMessage, message, mxit):
    ''' Handle for command 51 Receive invites '''
    from gui.invitewindow import InvitationWindow
    for info in message:
        if invitationWindows.has_key(info[0]):
            return
        invitationWindows[info[0]] = InvitationWindow(info, mxit)

class AcceptInviteMessage(ClientMessage):
    ''' Accepts a user invite '''
    def __init__(self, contactAddress, group='', nickname=''):
        self.command = 52
        self.message = [contactAddress, group, nickname]

class RejectInviteMessage(ClientMessage):
    ''' Rejects an invite '''
    def __init__(self, contactAddress):
        self.command = 55
        self.message = [contactAddress]

class KeepAliveMessage(ClientMessage):
    def __init__(self):
        self.command = 1000
