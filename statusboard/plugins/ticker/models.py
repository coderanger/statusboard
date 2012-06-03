from django.db import models
from django.utils.translation import ugettext_lazy as _

from statusboard.plugins import Plugin

class Ticker(Plugin):
    def css(self):
        yield 'ticker.css'

    def js(self):
        yield 'ticker.js'

    def render(self, request, opts):
        data = {
            'id': opts['id'],
            'library': opts.get('library'),
            'url': opts.get('url', ''),
        }
        if not data['library']:
            data['items'] = self.ticker_items(request, data)
        return 'ticker.html', data

    def ticker_items(self, request, data):
        pass