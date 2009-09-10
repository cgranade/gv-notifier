##
# preferences_window.py: Simple window for configuring gv_notifier.
##
# (c) 2009 Christopher E. Granade (cgranade@gmail.com).
# Licensed under GPL v3.
##

## IMPORTS #############################################################
import pygtk
pygtk.require("2.0")
import gtk

from configuration import Configuration

## CLASSES #############################################################
class PreferencesWindow():

    ## CONSTRUCTOR ##
    def __init__(self):
        self.conf = Configuration()
        self.win = gtk.Window()
        self.win.set_title("Google Voice Notifer Preferences")
    
        main_box = gtk.VBox()
        self.win.add(main_box)
        
        prefs_table = gtk.Table(rows=3,columns=2)
        main_box.add(prefs_table)
        
        uname_lbl = gtk.Label("Username:")
        prefs_table.attach(uname_lbl, 0, 1, 0, 1)
        passwd_lbl = gtk.Label("Password: ")
        prefs_table.attach(passwd_lbl, 0, 1, 1, 2)
        update_lbl = gtk.Label("Update interval: ")
        prefs_table.attach(update_lbl, 0, 1, 2, 3)
        
        self.uname_ety = gtk.Entry()
        prefs_table.attach(self.uname_ety, 1, 2, 0, 1)
        self.passwd_ety = gtk.Entry()
        self.passwd_ety.set_visibility(False)
        prefs_table.attach(self.passwd_ety, 1, 2, 1, 2)
        self.update_ety = gtk.Entry() # TODO: make spinbox
        prefs_table.attach(self.update_ety, 1, 2, 2, 3)
        
        btn_box = gtk.HBox()
        main_box.add(btn_box)
        
        self.ok_btn = gtk.Button("OK")
        self.cancel_btn = gtk.Button("Cancel")
        btn_box.add(self.ok_btn)
        btn_box.add(self.cancel_btn)
        
        self.ok_btn.connect("activate", self.on_ok_btn_activate)
        self.cancel_btn.connect("activate", self.on_cancel_btn_activate)
        
    ## PUBLIC METHODS ##
    def show(self):
        self.uname_ety.set_text(self.conf.get_username() or "")
        self.passwd_ety.set_text(self.conf.get_password() or "")
        self.update_ety.set_text(str(self.conf.get_updateinterval()))
        # TODO: don't show or reset if already here.
        self.win.show_all()
        
    ## EVENT HANDLERS ##
    def on_ok_btn_activate(self, button, data=None):
        self.conf.set_username(self.uname_ety.get_text())
        self.conf.set_password(self.passwd_ety.get_text())
        self.conf.set_updateinterval(int(self.update_ety.get_text()))
        # FIXME: not going away!
        self.win.hide_all()
        self.win.destroy()
        
    def on_cancel_btn_activate(self, button, data=None):
        # FIXME: not going away!
        self.win.hide_all()
        self.win.destroy()
        
