import select
import socket
from xml.dom import minidom

from django.db import models
from django.utils.translation import ugettext_lazy as _

from statusboard.plugins import Plugin
from statusboard.plugins.jenkins import conf
from statusboard.plugins.jenkins.utils import get_servers

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

    def server_url(self):
        if self.url:
            return self.url
        # Assume standard setup on port 8080 for lack of something better
        return 'http://%s:8080/'%self.ip


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
            'url': opts.get('url', ''),
            'jenkins_servers': get_servers(),
        }
        return 'jenkins.html', data

    def gather(self, url):
        pass

    def tick_60(self):
        if not conf.AUTOSERVERS:
            return # Manual servers config, don't scan the network
        AutoServer.objects.all().delete()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto('', ('<broadcast>', 33848))
        while 1:
            rready, wready, xready = select.select([sock], [], [], 1)
            if rready:
                data = sock.recvfrom(4096)
                AutoServer.objects.create_from_recvfrom(data)
            else:
                break
