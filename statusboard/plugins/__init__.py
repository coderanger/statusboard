import os
import os.path
import datetime
import traceback

from flask import Module

from statusboard.utils import import_module

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


def load_plugins(app):
    plugin_base = os.path.dirname(__file__)
    for name in os.listdir(plugin_base):
        path = os.path.join(plugin_base, name)
        if name.startswith('_'):
            continue
        if not os.path.isdir(path):
            continue
        if not os.path.isfile(os.path.join(path, '__init__.py')):
            continue
        print 'Loading plugin from %s'%('statusboard.plugins.'+name)
        try:
            mod = import_module('statusboard.plugins.'+name)
        except Exception:
            traceback.print_exc()
            continue
        for plugin in PluginMeta.plugins:
            if plugin.disable:
                continue
            plugin_name = plugin._plugin_name
            print 'Found plugin %s'%plugin_name
            plugin_registry[plugin_name] = {
                'name': plugin_name,
                'instance': plugin(),
                #'static': os.path.join(path, 'static'),
                #'templates': jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(path, 'templates')), auto_reload=True),
                'mod': mod.mod,
            }
            app.register_module(mod.mod, url_prefix='/plugin/'+plugin_name)
        PluginMeta.plugins = []

