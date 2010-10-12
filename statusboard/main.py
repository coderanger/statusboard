import datetime
import json
import os
import random
import traceback
from collections import namedtuple

from flask import request, session, render_template, Markup

from statusboard import app, db
from statusboard.utils import hex_random, add_new_widget
from statusboard.plugins import load_plugins, plugin_registry

class Settings(db.Model):
    __tablename__ = 'settings'
    username = db.Column(db.String(32), unique=True, primary_key=True)
    grid = db.Column(db.Text()) # JSON encoded data

class GatherRequest(db.Model):
    __tablename__ = 'gatherrequests'
    id = db.Column(db.Integer, primary_key=True)
    plugin = db.Column(db.String(32))
    username = db.Column(db.String(32))
    ts = db.Column(db.DateTime())
    util = db.Column(db.DateTime())
    arg = db.Column(db.Text())
    
    

# Settings = model('Settings',
#     user='string',
#     grid='string' # JSON encoded data
# )
# 
# GatherRequest = model('GatherRequest',
#     plugin='string',
#     user='string',
#     ts='datetime',
#     until='datetime',
#     arg='string',
# )

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
default_grid_json = json.dumps(default_grid)

def render_widget(opts, css_out=None, js_out=None):
    plugin = plugin_registry.get(opts['type'])
    if plugin is None:
        return render_error(opts)
    ret = plugin['instance'].render(opts)
    if len(ret) == 1:
        # Simple string
        return ret
    else:
        template_file, data = ret
        #template = plugin['mod'].get_template(template_file)
        #print template, render_template(template, **data)
        return render_template(plugin['name']+'/'+template_file, **data)

def render_error(opts):
    return render_template('widget_error.html', id=opts['id'], error='Type "%s" unknown'%opts['type'])

def load_settings():
    if 'name' not in session:
        session['name'] = hex_random(6)
    username = session['name']
    settings = Settings.query.filter_by(username=username).first()
    if not settings:
        settings = Settings(username=username, grid=default_grid_json)
        db.session.add(settings)
        db.session.commit()
    request.grid = json.loads(settings.grid)
    
    # For debugging
    if request.args.get('reset'):
        settings.grid = default_grid_json
        db.session.add(settings)
        db.session.commit()
        request.grid = default_grid
    return settings

LinkData = namedtuple('LinkData', ['name', 'path'])

@app.route('/')
def index():
    user_settings = load_settings()
    
    # Populate the widget library
    library = []
    css_files = set()
    js_files = set()
    for name, plugin in sorted(plugin_registry.iteritems()):
        for css in plugin['instance'].css():
            css_files.add(LinkData(name=plugin['name'], path=css))
        for js in plugin['instance'].js():
            js_files.add(LinkData(name=plugin['name'], path=js))
        output = Markup(render_widget({'type': name, 'id': 'library-'+name}))
        library.append({'output': output, 'name': name})
    
    # Render all the widgets we need
    for row in request.grid:
        for widget_opts in row:
            widget_opts['output'] = Markup(render_widget(widget_opts, css_files, js_files))
    data = {'grid': request.grid, 'library': library, 'css': css_files, 'js': js_files}
    return render_template('index.html', **data)

@app.route('/ajax/layout', methods=['POST'])
def ajax_layout():
    user_settings = load_settings()
    widgets = {}
    for row in request.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    new_grid = []
    row_count = request.form['rows']
    for i in xrange(int(row_count)):
        new_row = []
        row_data = request.form.getlist('row%s'%i)
        if not row_data:
            continue
        for widget_id in row_data:
            if widget_id in widgets:
                new_row.append(widgets[widget_id])
        new_grid.append(new_row)
    user_settings.grid = json.dumps(new_grid)
    db.session.add(user_settings)
    db.session.commit()
    return json.dumps({})

@app.route('/ajax/add', methods=['POST'])
def ajax_add():
    user_settings = load_settings()
    # Insert the new widget and set its type up
    print 'Adding at %s,%s'%(request.form['row'], request.form['before'])
    new_widget = add_new_widget(request.grid, int(request.form['row']), request.form['before'])
    new_widget['type'] = request.form['type']
    
    # Save the grid to the DB
    user_settings.grid = json.dumps(request.grid)
    db.session.add(user_settings)
    db.session.commit()
    
    # Render the new widget and send to the browser
    output = render_widget(new_widget)
    return json.dumps({'output': output})

@app.route('/ajax/config', methods=['POST'])
def ajax_config():
    user_settings = load_settings()
    # Build a lookup dict for the widgets
    widgets = {}
    for row in request.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    # Set the new options
    changed = set()
    for key, value in request.form.iteritems():
        if key.startswith('input_'):
            _, widget_id, name = key.split('_', 2)
            if widget_id in widgets:
                changed.add(widget_id)
                print 'Setting %s[%s] = %s'%(widget_id, name, value)
                widgets[widget_id][name] = value
    
    # Save the grid to the DB
    user_settings.grid = json.dumps(request.grid)
    db.session.add(user_settings)
    db.session.commit()
    
    # Render output
    output = {}
    for widget_id in changed:
        output[widget_id] = render_widget(widgets[widget_id])
    return json.dumps({'output': output})

@app.route('/ajax/reload', methods=['POST'])
def ajax_reload():
    user_settings = load_settings()
    # Build a lookup dict for the widgets
    widgets = {}
    for row in web.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    # Render output
    output = {}
    to_reload = request.form.getlist('widgets[]')
    #if not isinstance(to_reload, (list, tuple)):
    #    to_reload = [to_reload]
    for widget_id in to_reload:
        output[widget_id] = render_widget(widgets[widget_id])
    return json.dumps({'output': output})

@app.route('/debug/grid')
def debug_grid():
    from pprint import pformat
    user_settings = load_settings()
    return '<pre>'+pformat(web.grid)+'</pre>'

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')
    
@app.route('/gather')
def gather(web):
    append('<pre>')
    now = datetime.datetime.now()
    for gather in GatherRequest.find().all():
        db.session.delete(request)
        db.session.commit()
        #append('Processing %s,%s,%s\n'%(gather.plugin, gather.arg, gather.user))
        plugin = plugin_registry.get(request.plugin)
        if plugin is None:
            continue
        kwargs = {}
        if request.user:
            kwargs['user'] = request.user
        try:
            plugin['instance'].gather(request.arg, **kwargs)
        except Exception:
            traceback.print_exc()
        
        # Reshedule?
        if now < request.until:
            new_request = GatherRequest(plugin=request.plugin, user=request.user, ts=datetime.datetime.now(), until=request.until, arg=request.arg)
            new_request.save()
        
    append('</pre>')

load_plugins(app)

if __name__ == '__main__':
    import kronos
    s = kronos.ThreadedScheduler()
    def run_gather():
        import urllib2
        print 'Running gather'
        urllib2.urlopen('http://localhost:8000/gather').read()
    #s.add_interval_task(run_gather, 'run_gather', 60, 60, kronos.method.sequential, None, None)
    #s.start()
    app.secret_key = 'a'
    app.run(debug=True)
    #s.stop()