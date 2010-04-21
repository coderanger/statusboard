from statusboard.plugins import Plugin

class Clock(Plugin):
    def css(self):
        return 'clock.css'
    
    def js(self):
        return 'clock.js'
    
    def render(self, opts):
        data = {
            'id': opts['id'],
        }
        return 'clock.html', data

