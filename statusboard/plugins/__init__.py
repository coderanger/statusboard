import os
import os.path
import jinja2

plugin_registry = {}

class PluginMeta(type):
    plugins = []
    def __init__(cls, name, bases, d):
        super(PluginMeta, cls).__init__(name, bases, d)
        if name != 'Plugin':
            PluginMeta.plugins.append(cls)


class Plugin(object):
    __metaclass__ = PluginMeta


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
            plugin_name = plugin.__name__.lower()
            if plugin_name.endswith('plugin') or plugin_name.endswith('widget'):
                plugin_name = plugin_name[:-6]
            print 'Found plugin %s'%plugin_name
            plugin_registry[plugin_name] = {
                'name': plugin_name,
                'instance': plugin(),
                'static': os.path.join(path, 'static'),
                'templates': jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(path, 'templates')), auto_reload=True),
            }
        PluginMeta.plugins = []

