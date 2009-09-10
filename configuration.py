##
# configuration.py: Abstracts configuration backend.
##
# (c) 2009 Christopher E. Granade (cgranade@gmail.com).
# Licensed under GPL v3.
##
# TODO:
#   - Don't probe every time, but rely on notification.
#   - Implement GConf schema.
##

## IMPORTS #############################################################
import gconf

## CLASSES #############################################################
class Configuration():
    path = "/apps/gv-notifier/"

    def __init__(self):
        self.client = gconf.client_get_default()
        
    def get_username(self):
        return self.client.get_string(self.path + "username")
    def set_username(self, newval):
        self.client.set_string(self.path + "username", newval)
        
    def get_password(self):
        return self.client.get_string(self.path + "password")
    def set_password(self, newval):
        self.client.set_string(self.path + "password", newval)
        
    def get_updateinterval(self):
        return self.client.get_int(self.path + "updateInterval") or 15000
    def set_updateinterval(self, newval):
        self.client.set_int(self.path + "updateInterval", newval)
