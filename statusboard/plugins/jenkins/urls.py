from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^jobs/', 'statusboard.plugins.jenkins.views.jobs', name='statusboard-jenkins-jobs'),
    url(r'^timing/', 'statusboard.plugins.jenkins.views.timing', name='statusboard-jenkins-timing'),
)
