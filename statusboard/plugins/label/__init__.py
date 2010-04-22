from statusboard.plugins import Plugin

class Label(Plugin):
    def css(self):
        yield 'label.css'
    
    def render(self, opts):
        data = {
            'id': opts['id'],
            'label': opts.get('label', 'Label'),
            'link': opts.get('link', ''),
        }
        return 'label.html', data

