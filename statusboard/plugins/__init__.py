import os
import os.path
import datetime
import traceback

from django.utils.importlib import import_module

from statusboard.core.utils import guess_app

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
    disable = False
    namespace = None
    
    def css(self):
        return ()
    
    def js(self):
        return ()
    
    def gather_request(self, arg, user=None, run_for=300):
        from main import GatherRequest
        request = GatherRequest.find().filter_by(plugin=self._plugin_name, user=user, arg=arg).first()
        if not request:
            request = GatherRequest(plugin=self._plugin_name, user=user, ts=datetime.datetime.now(), until=datetime.datetime.now()+datetime.timedelta(seconds=run_for), arg=arg)
        else:
            request.until = datetime.datetime.now()+datetime.timedelta(seconds=run_for)
        request.save()


def urls_for_app(app):
    try:
        return import_module(app + '.urls')
    except ImportError:
        return None


def load_plugins():
    for plugin in PluginMeta.plugins:
        if plugin.disable:
            continue
        plugin_name = plugin._plugin_name
        print 'Found plugin %s'%plugin_name
        app = guess_app(plugin)
        plugin_registry[plugin_name] = {
            'name': plugin_name,
            'instance': plugin(),
            #'static': os.path.join(path, 'static'),
            #'templates': jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(path, 'templates')), auto_reload=True),
            'app': app,
            'urls': urls_for_app(app),
            'namespace': plugin.namespace or app.replace('.', '/'),
        }
    return plugin_registry
