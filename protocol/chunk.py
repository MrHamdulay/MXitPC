import struct
import mimetypes

from twisted.persisted import sob
from twisted.python import log

from protocol import constants
from gui.splashscreen import SplashScreen

''' Get a UTF-8 string from the data and return
    a tuple containing the message and whatever
    is left.
    
    Assumes that the first two bytes is the length'''
def getUTF8(data):
    length = struct.unpack('>H', data[:2])[0]
    string = data[2:length+2]
    return (string, data[length+2:])

def parseChunk(data, applicationSession):
    #Just so that loop will start
    chunkLength = 1
    position = 0
    while chunkLength > 0:
        chunkType = struct.unpack('b', data[position])[0]
        print 'We got chunk type %d'%chunkType
        length = struct.unpack('>i', data[position+1:position+5])[0]
        {constants.CHUNK_CUSTOM_RESOURCE: parseCustomResource,
         constants.CHUNK_SPLASH_IMAGE: parseSplashImage,
         constants.CHUNK_OFFER_FILE: parseOfferFile,
        }[chunkType](data[position+5:], length, applicationSession)
        position += length
        chunkLength -= length
    
#Custom resource is a container object for more chunks
def parseCustomResource(data, length, applicationSession):
    id, data = getUTF8(data)
    handle, data = getUTF8(data)
    operation = struct.unpack('b', data[0])[0]
    chunkLength = struct.unpack('>i', data[1:5])[0]
    
    data = data[5:]
    
    #ooh recursiveness!
    parseChunk(data, applicationSession)
    
    return chunkLength
    
def parseSplashImage(data, length, applicationSession):
    splash = [
    struct.unpack('b', data[0])[0], #Anchor
    struct.unpack('b', data[1])[0], #Time to show
    struct.unpack('>i', data[2:6])[0], #Bgcolout
    data[6:length] #Image data
    ]
    
    splashFile = sob.Persistent(splash, 'splash')
    splashFile.save(filename='splashScreen')
    
def parseOfferFile(data, length, applicationSession):
    log.msg('We don\'t have file support at the moment')
    
def sendFile(contactAddresses, filename, applicationSession):
    mime, encoding = mimetype.guess_type(filename)
