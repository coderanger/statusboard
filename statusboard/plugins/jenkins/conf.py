from django.conf import settings

AUTOSERVERS = getattr(settings, 'STATUSBOARD_JENKINS_AUTOSERVERS', True)

SERVERS = getattr(settings, 'STATUSBOARD_JENKINS_SERVERS', [])

TIME_ZONE = getattr(settings, 'STATUSBOARD_JENKINS_TIME_ZONE', getattr(settings, 'TIME_ZONE', 'UTC'))
