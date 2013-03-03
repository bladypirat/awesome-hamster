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
    _options = { }
    _options["name"] = 'myawehamsterbox'
    _options["format"] = '{activity}@{category} {currentHours}:{currentMinutes}'
    _options["default"] = 'no activity'
    _options["sbefore"] = '<span>'
    _options["safter"] = '</span>'
    _options["tag"] = None

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
        totalTime = 0
        tagTime = 0
        currentFact = None
        facts = self.ifaceHamster.GetTodaysFacts()

        if len(facts) > 0:
            for fact in facts:
                currentFact = {}
                currentFact["activity"] = str(fact[4])
                currentFact["category"] = str(fact[6])
                currentFact["tags"] = []
                for tag in fact[7]:
                    currentFact["tags"].append(str(tag))
                currentFact["startTime"] = int(fact[1])
                currentFact["endTime"] = int(fact[2])
                currentFact["elapsedTime"] = 0

                if currentFact["endTime"] == 0:
                    currentFact["elapsedTime"] = calendar.timegm(time.localtime()) - currentFact["startTime"]
                else:
                    currentFact["elapsedTime"] = currentFact["endTime"] - currentFact["startTime"]

                totalTime += currentFact["elapsedTime"]

                if self._options["tag"] is not None:
                    for tag in currentFact["tags"]:
                        if self._options["tag"] == tag:
                            tagTime += currentFact["elapsedTime"]

            totalMinutes = totalTime / 60
            totalHours = totalMinutes / 60
            totalMinutes = totalMinutes - (totalHours * 60)

            tagMinutes = 0
            tagHours = 0

            if self._options["tag"] is not None:
                tagMinutes = tagTime / 60
                tagHours = tagMinutes / 60
                tagMinutes = tagMinutes - (tagHours * 60)

        widgetTextFormat = '{widget}.text = \'{sbefore}{contents}{safter}\''
        widgetContents = ''

        if currentFact is None or currentFact["endTime"] != 0:
            print "No activity"
            widgetContents = 'no activity'
        else:
            currentMinutes = currentFact["elapsedTime"] / 60
            currentHours = currentMinutes / 60
            currentMinutes = currentMinutes - (currentHours * 60)
            widgetContents = self._options["format"].format(
                activity = currentFact["activity"], 
                category = currentFact["category"],  
                tag = self._options["tag"],
                currentHours = self._pretty_format(currentHours), 
                currentMinutes = self._pretty_format(currentMinutes), 
                totalHours = self._pretty_format(totalHours), 
                totalMinutes = self._pretty_format(totalMinutes), 
                tagHours = self._pretty_format(tagHours), 
                tagMinutes = self._pretty_format(tagMinutes)
                )
            print widgetContents

        widgetUpdate = widgetTextFormat.format(
            widget = self._options["name"], 
            sbefore = self._options["sbefore"],
            safter = self._options["safter"],
            contents = widgetContents
            )

        self.ifaceAwesome.Eval(widgetUpdate)

        print widgetUpdate

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
        opts,args = getopt.getopt ( argv, "n:f:t:d:b:a:", ["name=", "format=", "tag=", "default=", "before=", "after="] )

    except getopt.GetoptError:

        # catch invalid options and die
        print 'Invalid options'
        sys.exit(2)

    for opt,arg in opts:

        if opt == "-n":
            options['name'] = arg

        elif opt == "-f":
            # convert format string into something str.format() friendly
            arg = arg.replace("%a", "{activity}")
            arg = arg.replace("%c", "{category}")
            arg = arg.replace("%hc", "{currentHours}")
            arg = arg.replace("%mc", "{currentMinutes}")
            arg = arg.replace("%ht", "{totalHours}")
            arg = arg.replace("%mt", "{totalMinutes}")
            arg = arg.replace("%T", "{tag}")
            arg = arg.replace("%hT", "{tagHours}")
            arg = arg.replace("%mT", "{tagMinutes}")
            options['format'] = arg

        elif opt == "-b":
            options["sbefore"] = arg

        elif opt == "-a":
            print arg
            options["safter"] = arg

        elif opt == "-t":
            options["tag"] = arg

        elif opt == "-d":
            options["default"] = arg

    print options

    awehamster = AwesomeHamster ( options )
    awehamster.run()

if __name__ == "__main__":

    # call our main function and pass along all argv except
    # the first, since that's the name of the script
    main (sys.argv[1:])
