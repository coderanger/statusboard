from django.http import HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from statusboard.plugins.jenkins.models import Job
from statusboard.utils.json import JSONResponse

def jobs(request):
    server_url = request.GET.get('server_url')
    if not server_url:
        return HttpResponseBadRequest
    return JSONResponse({
        'jobs': Job.objects.filter(server_url=server_url),
        'label': _('Select a job'), # I don't like this, it belongs in the template
    })


def timing(request):
    return TemplateResponse(request, 'statusboard/plugins/jenkins/timing.html', {})
