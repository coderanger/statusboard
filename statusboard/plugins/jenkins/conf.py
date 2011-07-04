from django.conf import settings

AUTOSERVERS = getattr(settings, 'STATUSBOARD_JENKINS_AUTOSERVERS', True)

SERVERS = getattr(settings, 'STATUSBOARD_JENKINS_SERVERS', [])
