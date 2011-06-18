from django.contrib.auth.models import User
from django.db import models, connections
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from statusboard.core.db import JSONField

class Settings(models.Model):
    class Meta:
        db_table = 'statusboard_settings'
    user = models.ForeignKey(User, unique=True, related_name='statusboard_settings', verbose_name=_('user'))
    authenticated = models.BooleanField(_('authenticated'))
    grid = JSONField(_('grid'))


class ForUpdateQuerySet(QuerySet):
    def for_update(self):
        if 'sqlite' in connections[self.db].settings_dict['ENGINE'].lower():
            # Noop on SQLite since it doesn't support FOR UPDATE
            return self
        sql, params = self.query.get_compiler(self.db).as_sql()
        return self.model._default_manager.raw(sql.rstrip() + ' FOR UPDATE', params)


class ForUpdateManager(models.Manager):
    def get_query_set(self):
        return ForUpdateQuerySet(self.model, using=self._db)


class GatherRequest(models.Model):
    class Meta:
        db_table = 'statusboard_gatherrequests'
    plugin = models.CharField(_('plugin'), max_length=32)
    user = models.ForeignKey(User, unique=True, related_name='statusboard_gatherrequests', verbose_name=_('user'), null=True)
    ts = CreationDateTimeField(_('creation timestamp'))
    until = models.DateTimeField(_('run until timestamp'))
    args_hash = models.CharField(_('arguments hash'), max_length=40)
    args = JSONField(_('arguments'))

    objects = ForUpdateManager()
