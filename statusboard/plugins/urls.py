from django.conf.urls.defaults import patterns, url, include

from statusboard.plugins import plugin_registry

urlpatterns = patterns('')
for name, data in plugin_registry.iteritems():
    if data['urls']:
        urlpatterns.append(url(name+'/', include(data['urls'])))
