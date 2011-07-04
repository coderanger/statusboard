from statusboard.plugins.jenkins import conf

def get_servers():
    servers = conf.SERVERS[:]
    if conf.AUTOSERVERS:
        from statusboard.plugins.jenkins.models import AutoServer
        for server in AutoServer.objects.all():
            servers.append(server.server_url())
    return servers
