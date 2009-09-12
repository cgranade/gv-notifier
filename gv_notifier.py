##
# gv_notifier.py: small daemon that waits for GV messages
##
# (c) 2009 Christopher E. Granade (cgranade@gmail.com).
# Licensed under GPL v3.
##
# TODO:
#   - Document, document, document.
#   - Use appropriate icons.
#   - Clean up ClientLogin and get working.
##

## FUTURE ##############################################################
from __future__ import print_function

## IMPORTS #############################################################
import sys
import time
import urllib, urllib2, httplib, cookielib
import json

import pygtk
pygtk.require("2.0")
import gtk, gobject

import pynotify

from xml.dom import minidom

from gv_client import GoogleVoice, TooManyFailuresError
from configuration import Configuration
from preferences_window import PreferencesWindow

## UTILITY FUNCTIONS ###################################################
def parse_keys_list(listdata, keysep="\n"):
    keys = {}
    for key in listdata.split(keysep):
        if (len(key) > 0):
            keyparts = key.split("=", 1)
            if (len(keyparts) >= 2):
                keys[keyparts[0]] = keyparts[1]
    return keys
    
## CLASSES #############################################################
class Notifier():
    already_notified = []
    
    def main(self):
    
        # Start update loop and run it once manually.
        self.update_from_gv()
        self.update_loop_source = gobject.timeout_add(self.conf.get_updateinterval(),
            self.update_from_gv)

        # Enter the main loop.
        gtk.main()
        
    def __init__(self):
        # Load configuration stuff.
        self.conf = Configuration()
    
        # Config the status icon.
        self.statusicon = gtk.StatusIcon()        
            # TODO: set better icon.
        self.statusicon.set_from_stock("gtk-directory")
        
        # Make a menu for popping up later.
        self.popup_menu = self.make_menu()
        
        # Setup GV client.
        # TODO: allow first-time setup.
        username = self.conf.get_username()
        password = self.conf.get_password()
        self.gv = GoogleVoice(username, password)
        self.gv.login()
        
        # Connect event handlers.
        self.statusicon.connect("activate", self.on_status_activate)
        self.statusicon.connect("popup-menu", self.on_status_popup)
        
    def make_menu(self):
        menu = gtk.Menu()
        
        self.agr = gtk.AccelGroup()
        #self.add_accel_group(self.agr)
        
        pref_item = self.make_menu_item(menu, self.on_pref_item_activate, accel_key="P", icon=gtk.STOCK_PREFERENCES)
        quit_item = self.make_menu_item(menu, self.on_quit_item_activate, accel_key="Q", icon=gtk.STOCK_QUIT)
        
        return menu
         
    def make_menu_item(self, formenu, activate_cb, label=None, icon=None, accel_key=None, accel_grp=None):
        if icon:
            agr = accel_grp or self.agr
            item = gtk.ImageMenuItem(icon, agr)
            k, m = gtk.accelerator_parse(accel_key)
            item.add_accelerator("activate", agr, k, m, gtk.ACCEL_VISIBLE)
        elif label:
            item = gtk.MenuItem(label)
        else:
            # TODO: throw error
            return
        item.connect("activate", activate_cb)
        formenu.append(item)
        item.show()
        return item
         
    def update_from_gv(self):
        try:
            self.gv.update()
            self.make_notifications()
        except (TooManyFailuresError):
            sys.stderr.write(
                'Too many failures updating inbox. Waiting before next round of attempts.\n')
            self.display_error()
            
        return True # Make GTK run the update function again.

    def display_error(self):
        print('FIXME/TODO: implement display_error()!')

    def make_notifications(self):
        unread = self.gv.get_unread_msgs()
        unread_cnt = len(unread)
        
        if unread_cnt != self.gv.get_unread_msgs_count():
            print('[Warning] sanity check failed: unread_cnt != self.gv.get_unread_msgs_count()')
        
        self.statusicon.set_tooltip("%d unread messages." % unread_cnt)
        self.statusicon.set_blinking(unread_cnt > 0) # TODO: change to a different icon instead!
        
        for msg in unread:
            if msg.id not in self.already_notified:
                # TODO: what if icon is remote?
                self.already_notified.append(msg.id)
                n = pynotify.Notification("New Google Voice Message",
                    msg.markup(), msg.icon())
                n.attach_to_status_icon(self.statusicon)
                n.set_urgency(pynotify.URGENCY_NORMAL)
                n.set_timeout(3000)
                n.show()
    
    
    ## EVENT HANDLERS ##        
    def on_status_activate(self, icon, user_data=None):
        pass
        
    def on_status_popup(self, icon, button, activate_time, user_data=None):
        self.popup_menu.popup(None, None, None, button, activate_time, None)
        
    def on_pref_item_activate(self, item, user_data=None):
        # Load the preferences window.
        prefs_win = PreferencesWindow()
        prefs_win.show()

    def on_quit_item_activate(self, item, user_data=None):
        gtk.main_quit()
    
## MAIN CODE ###########################################################
if __name__ == "__main__":
    # Init PyNotify
    pynotify.init("Google Voice Notifier")
    
    # Make a Notifer and star it.
    notifier = Notifier()
    notifier.main()
    
