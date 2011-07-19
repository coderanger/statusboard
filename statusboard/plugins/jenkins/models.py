import select
import socket
import urllib2
from xml.dom import minidom

from django.db import models
from django.utils.translation import ugettext_lazy as _

from statusboard.plugins import Plugin
from statusboard.plugins.jenkins import conf
from statusboard.plugins.jenkins.utils import get_servers
from statusboard.utils import json

class AutoServerManager(models.Manager):
    def create_from_recvfrom(self, data_address):
        data, address = data_address
        fields = {'ip': address[0]}
        # Try to parse out a URL
        dom = minidom.parseString(data)
        urls = dom.getElementsByTagName('url')
        if urls:
            url = ''
            for n in urls[0].childNodes:
                if n.nodeType == n.TEXT_NODE:
                    url += n.data
            fields['url'] = url
        return self.create(**fields)


class AutoServer(models.Model):
    class Meta:
        db_table = 'statusboard_jenkins_autoservers'
    url = models.CharField(_('URL'), max_length=256)
    ip = models.CharField(_('IP'), max_length=256)

    objects = AutoServerManager()

    def __unicode__(self):
        return self.server_url()

    def __repr__(self):
        return '<AutoServer %s>'%self.server_url()

    def server_url(self):
        if self.url:
            return self.url
        # Assume standard setup on port 8080 for lack of something better
        return u'http://%s:8080/'%self.ip


class Job(models.Model):
    class Meta:
        db_table = 'statusboard_jenkins_jobs'
        unique_together = [('server_url', 'name')]
    server_url = models.CharField(_('server URL'), max_length=256)
    name = models.CharField(_('name'), max_length=256)
    url = models.CharField(_('URL'), max_length=256)
    status = models.NullBooleanField(_('status'), default=None)

    def to_dict(self):
        return {
            'id': self.id,
            'server_url': self.server_url,
            'name': self.name,
            'url': self.url,
        }


class Jenkins(Plugin):
    def css(self):
        yield 'cluetip-1.0.6/jquery.cluetip.css'
        yield 'jenkins.css'
    
    def js(self):
        yield 'jquery.hoverIntent.minified.js'
        yield 'cluetip-1.0.6/jquery.cluetip.min.js'
        yield 'jenkins.js'
    
    def render(self, request, opts):
        data = {
            'id': opts['id'],
            'server_url': opts.get('server_url', ''),
            'job': opts.get('job', ''),
            'servers': get_servers(),
            'jobs': [],
            'css_class': '',
        }
        if data['server_url']:
            data['jobs'] = Job.objects.filter(server_url=data['server_url'])
        if data['job']:
            try:
                data['job'] = Job.objects.get(id=data['job'])
                data['css_class'] = {True: 'green', False: 'red'}.get(data['job'].status, 'purple')
            except Job.DoesNotExist:
                data['job'] = ''
        return 'jenkins.html', data

    def gather(self, job_id):
        pass

    def tick_1(self, log):
        """Every minute, grab the jobs from all configured servers."""
        for server_url in get_servers():
            api_url = server_url+'api/json/?tree=jobs[name,url,healthReport[description,score],lastBuild[building,timestamp],lastCompletedBuild[result],lastSuccessfulBuild[duration]]'
            try:
                data = json.load(urllib2.urlopen(api_url))
            except urllib2.URLError:
                # Server unreachable, remove all jobs
                Job.objects.filter(server_url=server_url).delete()
                return
            jobs_seen = set()
            for job_data in data['jobs']:
                fields = {'url': job_data['url']}
                if 'lastCompletedBuild' in job_data:
                    result = job_data['lastCompletedBuild'].get('result')
                    if result is None:
                        fields['status'] = None
                    else:
                        fields['status'] = result == 'SUCCESS'
                job, created = Job.objects.get_or_create(server_url=server_url, name=job_data['name'], defaults=fields)
                if not created:
                    # Update to latest data
                    Job.objects.filter(id=job.id).update(**fields)
                jobs_seen.add(job.id)
            # Remove all jobs that we didn't see this time
            Job.objects.filter(server_url=server_url).exclude(id__in=jobs_seen).delete()

    def tick_60(self, log):
        """If AUTOSERVERS is enabled, scan the network every hour for available
        Jenkins servers.
        """
        if not conf.AUTOSERVERS:
            log.debug('AUTOSERVERS disabled, not performing network scan')
            return # Manual servers config, don't scan the network
        AutoServer.objects.all().delete()
        log.debug('Broadcasting for Jenkins servers')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto('', ('<broadcast>', 33848))
        while 1:
            rready, wready, xready = select.select([sock], [], [], 1)
            if rready:
                data = sock.recvfrom(4096)
                log.debug('Got response from Jenkins server %r', data)
                AutoServer.objects.create_from_recvfrom(data)
            else:
                break
