import datetime

from celery.task import task
from django.contrib.auth.models import User

from statusboard.core.models import GatherRequest
from statusboard.plugins import load_plugins, plugin_registry

load_plugins()

@task
def gather_request(plugin_name, user, args, kwargs):
    plugin = plugin_registry.get(plugin_name)
    if user:
        kwargs['user'] = User.objects.get(id=user)
    plugin['instance'].gather(*args, **kwargs)


@task
def gather_requests():
    log = gather_requests.get_logger()
    now = datetime.datetime.now()
    for gather in GatherRequest.objects.all().for_update():
        log.debug('Running gather request for plugin %s', gather.plugin)
        plugin = plugin_registry.get(gather.plugin)
        if plugin is None:
            log.warning('Plugin %s not found', gather.plugin)
            continue
        if gather.args is None:
            args = []
            kwargs = {}
        elif isinstance(gather.args, list):
            args = gather.args
            kwargs = {}
        else:
            args = ()
            kwargs = gather.args
        gather_request.apply_async(args=[gather.plugin, gather.user_id, args, kwargs])
        
        # Reshedule?
        if now >= gather.until:
            gather.delete()
