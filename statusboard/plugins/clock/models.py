from statusboard.plugins import Plugin

class Clock(Plugin):
    def css(self):
        yield 'clock.css'
    
    def js(self):
        yield 'clock.js'
    
    def render(self, request, opts):
        data = {
            'id': opts['id'],
        }
        return 'clock.html', data
