#!/usr/bin/env python
import dbus, dbus.mainloop.glib
import gobject
import time
import calendar
import sys
import getopt
from copy import deepcopy

# jQuery extend python port courtesy of 
# http://www.xormedia.com/recursively-merge-dictionaries-in-python/
def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result

class AwesomeHamster(gobject.GObject):

    # default options
    _options = { 'name' : 'myawehamsterbox' }

    def __init__(self,options=None):

        # initialise a dbus reciever
        gobject.GObject.__init__(self)
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus()
        self.bus.add_signal_receiver(self._on_facts_changed, 'FactsChanged', 'org.gnome.Hamster')

        # init the hamster and awesome dbus interfaces
        proxyHamster = self.bus.get_object('org.gnome.Hamster', '/org/gnome/Hamster')
        proxyAwesome = self.bus.get_object('org.naquadah.awesome.awful', '/')

        self.ifaceHamster = dbus.Interface(proxyHamster, 'org.gnome.Hamster')
        self.ifaceAwesome = dbus.Interface(proxyAwesome, 'org.naquadah.awesome.awful.Remote')

        # merge our default options with the ones provided
        if options is not None:          
            self._options = dict_merge ( self._options, options )

    def _pretty_format(self, number):
        if number < 10:
            return "0" + str(number)
        else:
            return str(number)

    def _on_facts_changed(self):
        self._refresh()

    def _refresh(self):
        startTime = 0
        facts = self.ifaceHamster.GetTodaysFacts()

        if len(facts) > 0:
            f = facts[-1]
            startTime = f[1]
            endTime = f[2]
            currentTime = calendar.timegm(time.localtime())
            elapsedTime = currentTime - startTime

        if startTime == 0 or endTime != 0:
            print "No activity"
            self.ifaceAwesome.Eval ( '%s.text = \'<span color=\"white\">  No activity  </span>\'' % (self._options['name']) )
        else:
            minutes = elapsedTime / 60
            hours = minutes / 60
            minutes = minutes - (hours * 60)
            print "%s@%s %s:%s" % (f[4], f[6], self._pretty_format(hours), self._pretty_format(minutes))
            self.ifaceAwesome.Eval('%s.text = \'<span color=\"white\">  %s@%s %s:%s  </span>\'' % (self._options['name'], f[4], f[6], self._pretty_format(hours), self._pretty_format(minutes)))

        return True

    def run(self):
        gobject.timeout_add_seconds(60, self._refresh)
        self._refresh()
        loop = gobject.MainLoop()
        loop.run()

def main(argv):

    options = {}

    try:

        # parse out valid options from argv
        opts,args = getopt.getopt ( argv, "n:", ["name="] )

    except getopt.GetoptError:

        # catch invalid options and die
        print 'Invalid options'
        sys.exit(2)

    for opt,arg in opts:
        if opt == "-n":
            options['name'] = arg

    awehamster = AwesomeHamster ( options )
    awehamster.run()

if __name__ == "__main__":

    # call our main function and pass along all argv except
    # the first, since that's the name of the script
    main (sys.argv[1:])