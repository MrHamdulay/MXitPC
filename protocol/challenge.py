from __future__ import with_statement
from twisted.web.client import getPage
from twisted.python import log
import time

RESOURCE_LOCATION = 'http://www.mxit.com/res/'

class CaptchaException(Exception):
    '''Thrown when Captcha isn't filled in correctly '''
    pass

class MXitServerException(Exception):
    '''Thrown when MXit returns an error '''
    pass

class Challenge:
    '''Class that does the challenge required by MXit server'''
    
    def __init__(self, errback):
        self.pid = None
        self.challengeData = None
        self.connectionInformation = None
        self.errback = errback

    def _requestData(self, data):
        if self.challengeData == None:
            baseUrl = RESOURCE_LOCATION
        else:
            baseUrl = self.challengeData['url']
    
        requestUrl = "%s?%s" % (baseUrl, '&'.join(
                    map(lambda x: "%s=%s"%(x[0], x[1]), data.iteritems())))
        
        defer = getPage(requestUrl).addCallback(lambda x: x.split(';'))
        return defer
        
    def requestChallenge(self, callback, requestCaptcha=True, requestLocales=True, requestCountries=True):
        '''Challenge the MXit server to reply with the product ID'''
        deferred = self._requestData({'type': 'challenge',
                           'getimage': str(requestCaptcha).lower(),
                           'getlanguage': str(requestLocales).lower(),
                           'getcountries': str(requestCountries).lower(),
                           'ts': time.time(),
                           })
        deferred.addErrback(self.errback)
        deferred.addCallback(self._requestChallenge)
        deferred.addCallback(callback)

    def parseMXitList(self, data):
        ''' Parses MXit list into one python can use.
        Used for country and language data'''
        parsed = []
        for item in data.split(','):
            parsed.append(item.split('|'))
        return parsed 
            
    def _requestChallenge(self, challengeData):
        '''Request challenge's callback '''
        if challengeData[0] != '0':
            raise MXitServerException
        
        if challengeData[1] != '':
            RESOURCE_LOCATION = challengeData[1]
        
        self.challengeData = {'url': challengeData[1],
                              'sessionid': challengeData[2],
                              'captcha': challengeData[3].decode('base64'),
                              'countries': self.parseMXitList(challengeData[4]),
                              'languages': self.parseMXitList(challengeData[5]),
                              'defaultCountry': challengeData[6],
                              'defaultCountryName': challengeData[7],
                              'defaultCountryCode': challengeData[8],
                              'regions': challengeData[9],
                              'defaultDialingCode': challengeData[10],
                              'defaultRegion': challengeData[11],
                              'defaultNPF': challengeData[12],
                              'defaultIPF': challengeData[13],
                              'defaultCity': challengeData[14],
                              }
        return self.challengeData

    def challengeReply(self, callback, challengeResponse, number, login=0, location='ZA', locale='en'):
        ''' Send reply to the challenge. server will reply with Product ID '''
        
        ''' We are currently using all the default locale and location values
            Todo: Request this information from user'''
        if login: self.category = '1'
        else: self.category = '0'
        self.loginname = number
        deferred = self._requestData({'type': 'getpid',
                                                 'sessionid': self.challengeData['sessionid'],
                                                 'ver': '5.8.2',
                                                 'login': number,
                                                 'cat': 'Y',
                                                 'chalresp': challengeResponse,
                                                 'cc': location, 
                                                 'loc': locale,
                                                 'path': self.category,
                                                 'ts': time.time()
                                  })
        deferred.addCallback(self._challengeReply)
        deferred.addCallback(callback)
        deferred.addErrback(self.errback)

    def _challengeReply(self, data):
        '''Challenge reply callback '''

        ''' Check error code '''
        if int(data[0]) == 1:
            print 'invalid captcha'
            self.challengeData['captcha'] = data[1].decode('base64')
            raise CaptchaException('Invalid captcha entry.')
        elif int(data[0]) == 2:
            print 'session expired'
            try:
                if data[2] == None:
                    pass
                self.challengeData['captcha'] = data[2].decode('base64')
                self.challengeData['sessionid'] = data[1]
            except:
                self.challengeData['captcha'] = data[1].decode('base64')
            
            raise MXitServerException('Session ID expired: Took too long to enter CAPTCHA, please try again')
        elif int(data[0]) == 3:
            print 'undefined error'
            raise MXitServerException('Undefined MXit Exception')
        elif int(data[0]) == 4:
            print 'internal mxit error'
            raise MXitServerException('Mxit Internal Mxit Server Error')
        elif int(data[0]) == 5:
            print 'invalid country code'
            raise MXitServerException('Invalid Country Code')
        elif int(data[0]) == 6:
            print 'not yet registered'
            self.challengeData['captcha'] = data[2].decode('base64')
            self.challengeData['sessionid'] = data[1]
            raise MXitServerException('Not yet registered: Wrong button selected')
        elif int(data[0]) == 7:
            print 'already registered'
            self.challengeData['captcha'] = data[2].decode('base64')
            self.challengeData['sessionid'] = data[1]
            raise MXitServerException('Already registered: Wrong button selected')

        ''' We now have all the information we need to log-in. Temporarily store it.'''
        if data[10] == '':
            data[10] = self.loginname
        self.connectionInformation = {'pid': data[1],
                                      'soc1': data[2],
                                      'http1': data[3],
                                      'dial': data[4],
                                      'npf': data[5],
                                      'ipf': data[6],
                                      'soc2': data[7],
                                      'http2': data[8],
                                      'keepalive': data[9],
                                      'loginname': data[10],
                                      'cc': data[11],
                                      'region': data[12],
                                      'isUtf8Disable': data[13],
                                      'category': self.category
                                      }
        return self.connectionInformation
