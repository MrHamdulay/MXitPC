'''
Created on May 11, 2009

@author: Yaseen
'''
from aes import AES
pyMxit = False
class Pin(object):
    '''
    Class that does all the Pin encryption
    '''
    encryptedPassword = None
    initialKey = "6170383452343567"

    def __init__(self, unencryptedPassword, pid):
        self.unencryptedPassword = unencryptedPassword
        self.pid = pid
        self.key = self.pad_key(pid[-8:])
        
        self.encrypt()

    def encrypt(self):
        #This isn't working as expected
        password = [ord(i) for i in "<mxit/>%s"%self.unencryptedPassword]
        
        pads = 16 - (len(password) % 16)
        password += [0] * (pads-1)
        password.append(pads)
        
        parts = self.split(password, 16)
        aes = AES()
        temp = []
        
        for part in parts:
            temp += aes.encrypt(part, self.key, aes.keySize["SIZE_128"])
            
        encrypted = ''.join([chr(i) for i in temp])
        self.encryptedPassword = encrypted.encode('base64').strip() 
        return self.encryptedPassword     
        
    def pad_key(self, key):
        ''' Pad key to 16 bytes '''
        key = [ord(item) for item in key][:16]
        initialKey = [ord(item) for item in self.initialKey]
        
        while len(key) < len(initialKey):
            key.append(initialKey[len(key)])
        
        assert len(key) == 16
        return key
    
    def split(self, seq, size):
        for i in range(0, len(seq), size):
            yield seq[i:i+size]
    
    def __str__(self):
        return str(self.encryptedPassword)
    