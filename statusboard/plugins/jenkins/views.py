from django.template.response import TemplateResponse

def timing(request):
    return TemplateResponse(request, 'statusboard/plugins/jenkins/timing.html', {})
