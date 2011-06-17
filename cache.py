from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
import urllib
import logging
import json


class MWrap(object):
    DEFAULT_TIMEOUT = 60 #1 min cache timeout

    def set(self, key, value):
        is_set = memcache.set(key, value, self.DEFAULT_TIMEOUT)
        if not is_set:
            logging.error('MEMFAIL set %s: %s' % key, value)
        return is_set 

    def delete(self, key):
        is_del = memcache.delete(key)
        if not is_del:
            logging.error('MEMFAIL delete %s' % key)
        return is_del 

    def get(self, key):
        is_get = memcache.get(key)
        if not is_get:
            logging.error('MEMFAIL get %s' % key)
        return is_get 


class Cache(webapp.RequestHandler):
    LINES = {
        'red': 'http://developer.mbta.com/Data/red.json',
        'orange': 'http://developer.mbta.com/Data/orange.json',
        'blue': 'http://developer.mbta.com/Data/blue.json',
    }

    def fetch_line(self, name):
        url = self.LINES.get(name)
        handle = urllib.urlopen(url)
        return handle.read()

    def format_line(self, data):
        warn = False
        data = json.loads(data)
        formatted_data = []
        expected_keys = ["Line", "Trip", "PlatformKey", "InformationType", "Time", "TimeRemaining", "Revenue", "Route"]
        errors = []
        for row in data:
            new_row = {}
            for key,value in row.iteritems():
                if not key in expected_keys:
                    warn = True
                    errors.append(key)
                new_row[key] = value
            formatted_data.append(new_row)
        if warn:
            pass #TODO: something
        return json.dumps(formatted_data)

    def get(self):
        c = MWrap()
        data = None
        data = c.get(self.line)
        if not data:
            data = self.format_line(self.fetch_line(self.line))
            c.set(self.line, data)
        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(data)
        
        

class RedLine(Cache):
    line = 'red'
class OrangeLine(Cache):
    line = 'orange'
class BlueLine(Cache):
    line = 'blue'


application = webapp.WSGIApplication(
    [('/line/red/', RedLine), ('/line/blue/', BlueLine), ('/line/orange/', OrangeLine)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
