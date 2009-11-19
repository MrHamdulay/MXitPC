class Contact:
    presence = None
    mood = None
    
    contactAddress = None
    nickname = None
    group = None
    presence = None
    mood = None
    contactType = None
    messageAvailable = False

    tab = None

    def __init__(self, contactAddress, nickname, group, presence, mood, contactType, messageAvailable):
        self.contactAddress = contactAddress
        self.nickname = nickname
        self.group = group
        self.presence = int(presence)
        self.mood = int(mood)
        self.contactType = int(contactType)
        self.messageAvailable = messageAvailable
        
    def __str__(self):
        return "<contact %s %s>" % (self.nickname, self.contactAddress)
        
    def __repr__(self):
        return self.__str__()
        
    def isGroup(self):
        #Todo: return real value
        return False
    
    def set_chat_tab(self, tab):
        self.tab = tab
        
    def deleteContact(self):
        pass

    def on_received_message(self, timestamp, type, message, id=0, flags=0):
        if self.tab == None:
            #Todo: create tab
            pass
        self.tab.receiveMessage(self.contactAddress, timestamp, type, message) 

    def on_contactUpdate(self, nickname, group, presence, mood, mxit):
        ''' Contact was updated (i.e presence, mood or nickname changed)
            activate required callbacks etc. '''
            
        #Check for changes
        if not nickname == self.nickname:
            self.nickname = nickname
            for callback in mxit['contactCallback']:
                callback(nickname, self, 'nickname')
                
        if not group == self.group:
            self.group = group
            for callback in mxit['contactCallback']:
                callback(group, self, 'group')
                
        if not presence == self.presence:
            self.presence = presence
            for callback in mxit['contactCallback']:
                callback(presence, self, 'presence')
    
        if not mood == self.mood:
            self.mood = mood
            for callback in mxit['contactCallback']:
                callback(mood, self, 'mood')
