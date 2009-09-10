##
# gv_client.py: Class for communicating with Google Voice.
##
# (c) 2009 Christopher E. Granade (cgranade@gmail.com).
# Licensed under GPL v3.
##

## FUTURE ##############################################################
from __future__ import print_function

## IMPORTS #############################################################
import urllib, urllib2, httplib, cookielib
import json

from xml.dom import minidom

## DEBUGGING ###########################################################
httplib.HTTPConnection.debuglevel = 2

## CONSTANTS ###########################################################
gv_inbox_url = "https://www.google.com/voice/inbox/recent/inbox/"
gv_login_url = "https://www.google.com/accounts/ServiceLoginAuth"
gv_login_host = "www.google.com"
gv_login_path = "/accounts/ServiceLoginAuth?service=grandcentral"

cl_url = "https://www.google.com/accounts/ClientLogin"
cl_host = "www.google.com"
cl_path = "/accounts/ClientLogin"

url_encoded = "application/x-www-form-urlencoded"
       
       
## CONSTANTS ###########################################################

# TODO: Change these paths to something reasonable.

icons = {
    "sms": "file:///home/cgranade/projects/toy-projects/gv-notifier/sms-icon.png",
    "voicemail": "file:///home/cgranade/projects/toy-projects/gv-notifier/voicemail-icon.png"
}

## CLASSES #############################################################

class TooManyFailuresError(Exception):
    def __init__(self, num, url):
        self.url = url
        self.num = num
        
    def __str__(self):
        return "Too many failures (%d) fetching url: %s" % (self.num, self.url)

class GoogleVoice():
    # CONFIGURATION
    try_clientlogin = False
    try_servicelogin = True
    debuglevel = 0
    use_cookies = False
    cookies_whitelist = ["LSID", "SSID", "SID", "GAUSR", "HSID", "CAL"]
    
    # MEMBER VARIABLES
    auth_key = False
    username = None
    password = None
    cookies = {}
    cj = cookielib.CookieJar()
    
    feed_cache = None
    
    # CONSTRUCTOR
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))

    def _debug(self, level, msg):
        if level <= self.debuglevel:
            print(msg)

    # LOGIN METHODS
    def login(self):
        if self.try_clientlogin:
            self._debug(1, "Trying ClientLogin.")
            self.cl_login()
        if self.try_servicelogin:
            self._debug(1, "Trying reverse-engineered ServiceLogin.")
            self.gv_login()
            
    def gv_login(self, path=gv_login_path):
        # TODO: Check for valid response.
    
        params = urllib.urlencode({
            "service": "grandcentral",
            "Email": self.username,
            "Passwd": self.password
        })
        
        request = urllib2.Request(gv_login_url + "?" + params)
        response = self.opener.open(request)
        
        return

    def cl_login(self):
        params = urllib.urlencode({
            "accountType": "HOSTED_OR_GOOGLE",
            "Email": self.username,
            "Passwd": self.password,
            "service": "grandcentral", # Is this right?
            "source": "cgranade-gv_notifier-0.1"
        })
        headers = {"Content-type": url_encoded,
                   "Accept:": "text/plain"}
                   
        conn = httplib.HTTPSConnection(cl_host)
        conn.request("POST", cl_path, params, headers)
        response = conn.getresponse()
        if response.status != 200:
            print(response.status, response.reason)
            conn.close()
            return # TODO: Should throw an exception
        else:
            respdata = response.read()  
            keys = parse_keys_list(respdata)
            self.auth_key = keys["Auth"]
            conn.close()

    # FEED FETCHING METHODS
    def get_authorized(self, url):
        # Setup the request
        request = urllib2.Request(url)
        
        # Present authentication if any.
        if self.auth_key:
            request.add_header('Authorization',
                'GoogleLogin auth=%s' % self.auth_key)
                
        if self.use_cookies:
            for (name, val) in self.cookies.items():
                self._debug(2, "Sending cookie %s = %s" % (name,val))
                request.add_header('Cookie',
                    '%s=%s' % (name,val))
                        
        # NOTE: This may throw an error, but it's best to catch it outside of here.
        response = self.opener.open(request)            
        
        max_tries = 5 # TODO: make this a constant or config option
        tries = 0
        
        data = None
        
        while not data and (tries < max_tries):
            try:
                data = response.read()
            except httplib.IncompleteRead:
                tries = tries + 1
                data = None
                
        if data:
            return data
        else:
            raise TooManyFailuresError(tries, url)
        
    def get_inbox_raw(self):
        return self.get_authorized(gv_inbox_url)
        
    def get_inbox_feed_from_server(self):
        data = self.get_inbox_raw()
        doc = minidom.parseString(data)
        jsonelem = doc.getElementsByTagName('json')[0]
        htmlelem = doc.getElementsByTagName('html')[0]
        return Feed(jsonelem, htmlelem)
        
    def update(self):
        try:
            self.feed_cache = self.get_inbox_feed_from_server()
        except urllib2.URLError as err:
            print('Could not update: %s' % err)
        except TooManyFailuresError as err:
            print('Could not update: %s' % err)
        
    def get_inbox_feed(self):
        if not self.feed_cache:
            self.update()
        return self.feed_cache
        
    def get_unread_counts(self):
        return self.get_inbox_feed().get_unread_counts()
        
    def get_msgs(self, cond=(lambda x: True)):
        return self.get_inbox_feed.get_msgs(cond)
        
    def get_unread_msgs(self):
        return self.get_inbox_feed().get_unread_msgs()
        
    def get_unread_msgs_count(self):
        return self.get_unread_counts()["all"]
        
class Feed():
    def __init__(self, json_e, html_e):
        self.json = json.loads(json_e.firstChild.data)

        # UGLY HACK #
        ugly_hack_data =  '''<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE html
                PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
                "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
            %s
            </html>
            ''' % html_e.firstChild.data.replace("&copy;", "").replace("hl=en&answer","")
        self.html = minidom.parseString(ugly_hack_data)
        
    def get_unread_counts(self):
        return self.json["unreadCounts"]
        
    def get_msgs(self, cond=(lambda x: True)):
        jsonmsgs = self.json["messages"]
        msgs = []
        for (msg_id, msg_content) in jsonmsgs.items():
            if cond(msg_content):                
                # Find the matching div in the html element.
                divs = [div for div
                            in self.html.getElementsByTagName("div")
                            if ("id" in div.attributes.keys()) and (div.attributes["id"].value == msg_id)]
                
                if len(divs) != 1:
                    # TODO: throw an error.
                    print("Found %d divs for msg %s." % (len(divs), msg_id))
                    div = None
                    divattrs = [div.attributes for div in self.html.getElementsByTagName("div")
                            if "id" in div.attributes.keys()]
                    # print(map(lambda div: (map(lambda attr: (attr.name, attr.value), div.values())), divattrs[0:10]))
                else:
                    div = divs[0]
                
                msgs.append(Message(msg_id, msg_content, div))
                
        return msgs
        
    def get_unread_msgs(self):
        return self.get_msgs(lambda x: not x["isRead"])
    
def xml_attr_match(elem, name, value):
    return name in elem.attributes.keys() and elem.attributes[name].value == value
    
class Message():
    def __init__(self, msgid, content, htmldiv):
        self.id = msgid
        self.content = content
        self.htmldiv = htmldiv
        
    def is_sms(self):
        return u"sms" in self.content["labels"]

    def is_voicemail(self):
        return u"voicemail" in self.content["labels"]
        
    def sender_name(self):
        # Find span/@class=gc-message-name/a
        spans = [span for span
                      in self.htmldiv.getElementsByTagName("span")
                      if xml_attr_match(span, "class", "gc-message-name")]
        if len(spans) != 1:
            print("Found %d <spans>s with class 'gc-message-name'." % len(spans))
            return None
            
        span = spans[0]
        
        links = span.getElementsByTagName("a")
        if len(links) == 0: # No associated contact
            return span.getElementsByTagName("span")[0].firstChild.data
        else:
            return links[0].firstChild.data
        
    def sender_icon(self):
        # Find div/@class=gc-message-portrait/img@src
        divs = [div for div
                    in self.htmldiv.getElementsByTagName("div")
                    if xml_attr_match(div, "class", "gc-message-portrait")]
        if len(divs) != 1:
            print("Found %d <div>s with class 'gc-message-portrait'." % len(divs))
            return None
            
        div = divs[0]
        
        return "http://www.google.com" + div.getElementsByTagName("img")[0].attributes["src"].value
        
        
    def markup(self):
        # "From <b>%s</b> <b>%s<b>. <i>%s</i>"
        markup = "From %s %s.\nLabels: %s" % (
            self.sender_name(),
            self.content["relativeStartTime"],
            ", ".join(self.content["labels"])
        )
        return markup
        
    def icon(self):
        si = self.sender_icon()
        if si:
            return si
        elif self.is_sms():
            return icons["sms"]
        elif self.is_voicemail():
            return icons["voicemail"]  
        else:
            return ""
        
