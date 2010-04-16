import time
from statusboard.plugins import Plugin

class Clock(Plugin):
    def css(self, opts):
        return 'clock.css'
    
    def js(self, opts):
        return 'clock.js'
    
    def render(self, opts):
        data = {
            'id': opts['id'],
        }
        return 'clock.html', data

