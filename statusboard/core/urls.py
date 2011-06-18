from django.conf.urls.defaults import patterns, url, include

from statusboard.plugins import load_plugins

load_plugins()

urlpatterns = patterns('',
    url(r'^plugin/', include('statusboard.plugins.urls')),
    url(r'^ajax/layout', 'statusboard.core.views.ajax_layout', name='statusboard_ajax_layout'),
    url(r'^ajax/add', 'statusboard.core.views.ajax_add', name='statusboard_ajax_add'),
    url(r'^ajax/config', 'statusboard.core.views.ajax_config', name='statusboard_ajax_config'),
    url(r'^ajax/reload', 'statusboard.core.views.ajax_reload', name='statusboard_ajax_reload'),
    url(r'^$', 'statusboard.core.views.index', name='statusboard_index'),
)
