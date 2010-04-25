from statusboard.plugins import Plugin

class Upcoming(Plugin):
    def css(self):
        yield 'upcoming.css'
    
    def js(self):
        yield 'upcoming.js'
    
    def render(self, opts):
        data = {
            'id': opts['id'],
            'url': opts.get('url', ''),
        }
        return 'upcoming.html', data

