import os
import os.path
import datetime
import jinja2

plugin_registry = {}

class PluginMeta(type):
    plugins = []
    def __init__(cls, name, bases, d):
        super(PluginMeta, cls).__init__(name, bases, d)
        if name != 'Plugin':
            name = name.lower()
            if name.endswith('plugin') or name.endswith('widget'):
                cls._plugin_name = name[:-6]
            else:
                cls._plugin_name = name
            PluginMeta.plugins.append(cls)


class Plugin(object):
    __metaclass__ = PluginMeta
    
    def css(self):
        pass
    
    def js(self):
        pass
    
    def gather_request(self, arg, user=None):
        from main import GatherRequest
        request = GatherRequest(plugin=self._plugin_name, user=user, ts=datetime.datetime.now(), arg=arg)
        request.save()


def load_plugins():
    plugin_base = os.path.dirname(__file__)
    for name in os.listdir(plugin_base):
        path = os.path.join(plugin_base, name)
        if not os.path.isdir(path):
            continue
        if not os.path.isfile(os.path.join(path, '__init__.py')):
            continue
        print 'Loading plugin from %s'%('statusboard.plugins.'+name)
        __import__('statusboard.plugins.'+name, None, None, [''])
        for plugin in PluginMeta.plugins:
            plugin_name = plugin._plugin_name
            print 'Found plugin %s'%plugin_name
            plugin_registry[plugin_name] = {
                'name': plugin_name,
                'instance': plugin(),
                'static': os.path.join(path, 'static'),
                'templates': jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(path, 'templates')), auto_reload=True),
            }
        PluginMeta.plugins = []

