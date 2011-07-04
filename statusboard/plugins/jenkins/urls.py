from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^timing/', 'statusboard.plugins.jenkins.views.timing'),
)
