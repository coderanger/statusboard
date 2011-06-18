from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from statusboard.core.db import JSONField

class Settings(models.Model):
    class Meta:
        db_table = 'statusboard_settings'
    user = models.ForeignKey(User, unique=True, related_name='statusboard_settings', verbose_name=_('user'))
    authenticated = models.BooleanField(_('authenticated'))
    grid = JSONField(_('grid'))


class GatherRequest(models.Model):
    class Meta:
        db_table = 'statusboard_gatherrequests'
    plugin = models.CharField(_('plugin'), max_length=32)
    user = models.ForeignKey(User, unique=True, related_name='statusboard_gatherrequests', verbose_name=_('user'))
    ts = CreationDateTimeField(_('creation timestamp'))
    until = models.DateTimeField(_('run until timestamp'))
    arg = JSONField(_('argument'))
