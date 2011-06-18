import datetime
import json
import traceback
from collections import namedtuple

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from statusboard.core.models import Settings, GatherRequest
from statusboard.core.utils import hex_random, add_new_widget
from statusboard.plugins import load_plugins, plugin_registry

default_grid = [
    [
        {'type': 'label', 'id': '1'}, 
        #{'type': 'builder', 'id': '2'},
        #{'type': 'builder', 'id': '3'},
    ],
    [
        {'type': 'label', 'id': '4'},
        #{'type': 'builder', 'id': '5'},
        #{'type': 'builder', 'id': '6'},
    ],
]

class JSONResponse(HttpResponse):
    def __init__(self, obj, **kwargs):
        super(self, JSONResponse).__init__(json.dumps(obj), mimetype='application/json', **kwargs)


def render_widget(request, opts, css_out=None, js_out=None):
    plugin = plugin_registry.get(opts['type'])
    if plugin is None:
        return render_error(request, opts)
    ret = plugin['instance'].render(request, opts)
    if len(ret) == 1:
        # Simple string
        return ret
    else:
        template_file, data = ret
        #template = plugin['mod'].get_template(template_file)
        #print template, render_template(template, **data)
        template = loader.get_template(plugin['namespace']+'/'+template_file)
        return template.render(RequestContext(request, data))

def render_error(request, opts):
    template = loader.get_template('widget_error.html')
    return template.render(RequestContext(request, {
        'id': opts['id'], 
        'error': _('Type "%s" unknown')%opts['type'],
        }))

def load_settings(request):
    if request.user.is_authenticated():
        user = request.user
    else:
        # Key anonymous users off their session ID
        if 'name' not in request.session:
            request.session['name'] = hex_random(16)
        try:
            user = User.objects.get(username=request.session['name'])
        except User.DoesNotExist:
            user = User.objects.create(username=request.session['name'], password='', email='')
    settings, settings_created = Settings.objects.get_or_create(user=user, authenticated=request.user.is_authenticated(), defaults={'grid': default_grid})
    request.grid = settings.grid
    request.statusboard_user = user

    # For debugging
    if request.GET.get('reset'):
        request.grid = settings.grid = default_grid
        settings.save()
    return settings

LinkData = namedtuple('LinkData', ['name', 'path'])

def index(request):
    load_settings(request)
    
    # Populate the widget library
    library = []
    css_files = set()
    js_files = set()
    for name, plugin in sorted(plugin_registry.iteritems()):
        for css in plugin['instance'].css():
            css_files.add(LinkData(name=plugin['name'], path=plugin['namespace'] + '/' + css))
        for js in plugin['instance'].js():
            js_files.add(LinkData(name=plugin['name'], path=plugin['namespace'] + '/' + js))
        output = render_widget(request, {'type': name, 'id': 'library-'+name})
        library.append({'output': output, 'name': name})
    
    # Render all the widgets we need
    for row in request.grid:
        for widget_opts in row:
            widget_opts['output'] = render_widget(request, widget_opts, css_files, js_files)
    data = {'grid': request.grid, 'library': library, 'css': css_files, 'js': js_files}
    return TemplateResponse(request, 'index.html', data)


def ajax_layout(request):
    user_settings = load_settings(request)
    widgets = {}
    for row in request.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    new_grid = []
    row_count = request.POST['rows']
    for i in xrange(int(row_count)):
        new_row = []
        row_data = request.POST.getlist('row%s'%i)
        if not row_data:
            continue
        for widget_id in row_data:
            if widget_id in widgets:
                new_row.append(widgets[widget_id])
        new_grid.append(new_row)
    user_settings.grid = new_grid
    user_settings.save()
    return HttpResponse(json.dumps({}), mimetype='application/json')


def ajax_add(request):
    user_settings = load_settings(request)
    # Insert the new widget and set its type up
    print 'Adding at %s,%s'%(request.POST['row'], request.POST['before'])
    new_widget = add_new_widget(request.grid, int(request.POST['row']), request.POST['before'])
    new_widget['type'] = request.POST['type']
    
    # Save the grid to the DB
    user_settings.grid = request.grid
    user_settings.save()
    
    # Render the new widget and send to the browser
    output = render_widget(request, new_widget)
    return HttpResponse(json.dumps({'output': output}), mimetype='application/json')


def ajax_config(request):
    user_settings = load_settings(request)
    # Build a lookup dict for the widgets
    widgets = {}
    for row in request.grid:
        for widget in row:
            widgets[widget['id']] = widget

    # Set the new options
    changed = set()
    for key, value in request.POST.iteritems():
        if key.startswith('input_'):
            _, widget_id, name = key.split('_', 2)
            if widget_id in widgets:
                changed.add(widget_id)
                print 'Setting %s[%s] = %s'%(widget_id, name, value)
                widgets[widget_id][name] = value
    
    # Save the grid to the DB
    user_settings.grid = request.grid
    user_settings.save()
    
    # Render output
    output = {}
    for widget_id in changed:
        output[widget_id] = render_widget(request, widgets[widget_id])
    return HttpResponse(json.dumps({'output': output}), mimetype='application/json')


def ajax_reload(request):
    load_settings(request)
    # Build a lookup dict for the widgets
    widgets = {}
    for row in request.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    # Render output
    output = {}
    to_reload = request.POST.getlist('widgets[]')
    #if not isinstance(to_reload, (list, tuple)):
    #    to_reload = [to_reload]
    for widget_id in to_reload:
        output[widget_id] = render_widget(request, widgets[widget_id])
    return JSONResponse({'output': output})

# @app.route('/debug/grid')
# def debug_grid():
#     from pprint import pformat
#     user_settings = load_settings()
#     return '<pre>'+pformat(web.grid)+'</pre>'

# @app.route('/favicon.ico')
# def favicon():
#     return app.send_static_file('favicon.ico')
    
# @app.route('/gather')
# def gather(web):
#     append('<pre>')
#     now = datetime.datetime.now()
#     for gather in GatherRequest.find().all():
#         db.session.delete(request)
#         db.session.commit()
#         #append('Processing %s,%s,%s\n'%(gather.plugin, gather.arg, gather.user))
#         plugin = plugin_registry.get(request.plugin)
#         if plugin is None:
#             continue
#         kwargs = {}
#         if request.user:
#             kwargs['user'] = request.user
#         try:
#             plugin['instance'].gather(request.arg, **kwargs)
#         except Exception:
#             traceback.print_exc()
        
#         # Reshedule?
#         if now < request.until:
#             new_request = GatherRequest(plugin=request.plugin, user=request.user, ts=datetime.datetime.now(), until=request.until, arg=request.arg)
#             new_request.save()
        
#     append('</pre>')

# load_plugins(app)

# @celery.task()
# def add(x, y):
#     return x + y

# @app.route("/add")
# def add_view(x=16, y=16):
#     x = int(request.args.get("x", x))
#     y = int(request.args.get("y", y))
#     res = add.apply_async((x, y))
#     from flask import escape
#     context = {"id": res.task_id, "x": x, "y": y, 'res': escape(repr(res))}
#     return """Hello world: \
#                 add(%(x)s, %(y)s) = \
#                 <a href="/result/%(id)s">%(id)s</a><br /><pre>%(res)s</pre>""" % context

# @app.route("/result/<task_id>")
# def show_result(task_id):
#     retval = add.AsyncResult(task_id).get(timeout=1.0)
#     return repr(retval)

# if __name__ == '__main__':
#     import kronos
#     s = kronos.ThreadedScheduler()
#     def run_gather():
#         import urllib2
#         print 'Running gather'
#         urllib2.urlopen('http://localhost:8000/gather').read()
#     #s.add_interval_task(run_gather, 'run_gather', 60, 60, kronos.method.sequential, None, None)
#     #s.start()
#     app.secret_key = 'a'
#     app.run(debug=True)
#     #s.stop()