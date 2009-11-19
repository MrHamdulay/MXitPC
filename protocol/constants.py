'''
Created on May 2, 2009

@author: Yaseen
'''
import sys

APPLICATION_VERSION = '0.1'

MAX_REPLY_LEN = 100000
DISTRIBUTOR_CODE = 'R'
PROTOCOL_VERSION = '5.8.2'
ARCH_SERIES = 'Y' #PC Client
#PLATFORM = "%s_%s"%(sys.platform, APPLICATION_VERSION)
PLATFORM = 'PC'

VERSION = '%s-%s-%s-%s' % (DISTRIBUTOR_CODE, PROTOCOL_VERSION, ARCH_SERIES, PLATFORM)

#Login Constants
GET_CONTACTS = '1' # 1 - Don't retrieve contacts, this is going to be in a separate thingy to simplify things
                   # 0 - Retrieve contacts
CAPABILITIES = 'utf8=true;ctyp=%d' % (0x1|0x2|0x4|0x8|0x10|0x20|0x200)

FEATURES = 0x1|0x2|0x8|0x20|0x200|0x1000|0x200|0x8000|0x10000|0x20000|0x40000

#Prescence
OFFLINE = 0
ONLINE = 1
AWAY = 2
BUSY = 4
PRESENCE = ['offline', 'online', 'away', 'DND', 'busy']

MESSAGE_TYPE_NORMAL = 1
MESSAGE_TYPE_CHAT = 2
MESSAGE_TYPE_HEADLINE = 3
MESSAGE_TYPE_ERROR = 4
MESSAGE_TYPE_GROUPCHAT = 5
MESSAGE_TYPE_MXIT_CUSTOM_FORM = 6
MESSAGE_TYPE_MXIT_COMMAND = 7

#Mood
NO_MOOD = 0
ANGRY = 1
EXCITED = 2
GRUMPY = 3
HAPPY = 4
IN_LOVE = 5
INVINCIBLE = 6
SAD = 7
HOT = 8
SICK = 9
SLEEPY = 10
MOODS = ['none', 'angry', 'excited', 'grumpy', 'happy', 'inlove', 
         'invincible', 'sad', 'hot', 'sick', 'sleepy']

#Type
CONTACT_TYPE_MXIT = 0
CONTACT_TYPE_JABBER = 1
CONTACT_TYPE_MSN = 2
CONTACT_TYPE_YAHOO = 3
CONTACT_TYPE_ICQ = 4
CONTACT_TYPE_AIM = 5
CONTACT_TYPE_BOT = 8
CONTACT_TYPE_CHATROOM = 9
CONTACT_TYPE_GALLERY = 12
CONTACT_TYPE_INFO = 13
CONTACT_TYPE_MULTIMIX = 14
CONTACT_TYPE_GOOGLE_TALK = 18

#Chunks
CHUNK_NONE = 0x00
CHUNK_CUSTOM_RESOURCE = 0x01
CHUNK_SPLASH_IMAGE = 0x02
CHUNK_SPLASH_CLICK_THROUGH = 0x03
CHUNK_OFFER_FILE = 0x06
CHUNK_REJECT_FILE = 0x07
CHUNK_GET_FILE = 0x08
CHUNK_RECEIVED_FILE = 0x09
CHUNK_SEND_DIRECT = 0x0A
CHUNK_FORWARD_FILE_DIRECT = 0x0B
CHUNK_SKIN = 0x0C
CHUNK_END = 0x7E
CHUNK_EXTENDED_TYPE = 0x7F

CHUNK_OP_UPDATE = 0
CHUNK_OP_REMOVE = 1


COMMANDS = {1: 'login',
                         2: 'logout',
                         3: 'get_contacts',
                         5: 'update_contact_info',
                         6: 'invite_contact',
                         8: 'remove_contact',
                         9: 'receive_messages',
                         10: 'send_message',
                         11: 'register',
                         12: 'update_profile',
                         17: 'poll_difference',
                         26: 'get_profile',
                         27: 'get_multimedia_message',
                         29: 'rename_group',
                         30: 'remove_group',
                         31: 'splash_click_through',
                         32: 'set_prescence_status',
                         33: 'block_contact',
                         34: 'broadcast_message',
                         41: 'set_mood',
                         43: 'login_kick',
                         44: 'create_multimix',
                         45: 'add_to_multimix',
                         51: 'got_invite',
                         52: 'accept_invite',
                         54: 'register_gateway',
                         55: 'reject_contact',
                         56: 'unregister_gateway',
                         1000: 'keep_alive'}
