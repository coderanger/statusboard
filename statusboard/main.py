import random
import simplejson
from juno import *
import werkzeug
init({ 'db_type': 'sqlite', 
       'db_location': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'webapp.db'),
       'use_debugger': True,
       'mode': 'wsgi',
       'static_expires': 60*60,
       'app_path': os.path.abspath(os.path.dirname(__file__)),
       'use_sessions': True,
       'session_secret': 'ASDFQW$FAQWEFASD',
     })

from utils import hex_random, add_new_widget
     
Builder = model('Builder', 
    name='string',
    ts='datetime',
    state='string',
    broken_ts='datetime',
    current_gimme='string',
    current_svn='string',
    last_full_time='integer',
    current_time='integer',
    last_build='string',
    gimme_branch='string',
    svn_branch='string'
)

Settings = model('Settings',
    user='string',
    grid='string' # JSON encoded data
)

default_grid = [
    [
        {'type': 'label', 'id': '1'}, 
        {'type': 'builder', 'id': '2'},
        {'type': 'builder', 'id': '3'},
    ],
    [
        {'type': 'label', 'id': '4'},
        {'type': 'builder', 'id': '5'},
        {'type': 'builder', 'id': '6'},
    ],
]
default_grid_json = simplejson.dumps(default_grid)

def render_builder(opts):
    data = {
        'id': opts['id'],
        'label': opts.get('label', 'Builder'),
        'progress': random.randint(1, 100),
    }
    return render_template(get_template('widget_builder.html'), **data)

def render_label(opts):
    data = {
        'id': opts['id'],
        'label': opts.get('label', 'Label'),
        'link': opts.get('link', ''),
    }
    return render_template(get_template('widget_label.html'), **data)

def render_error(opts):
    return render_template(get_template('widget_error.html'), id=opts['id'], error='Type %s unkown'%opts['type'])

widget_types = {
    'builder': render_builder,
    'label': render_label,
}

def load_settings(web):
    if 'name' not in web.session:
        web.session['name'] = hex_random(6)
        web.session.save()
    user_name = web.session['name']
    user_settings = Settings.find().filter_by(user=user_name).first()
    if not user_settings:
        user_settings = Settings(user=user_name, grid=default_grid_json)
        user_settings.save()
    web.grid = simplejson.loads(user_settings.grid)
    
    # For debugging
    if web.input('reset'):
        user_settings.grid = default_grid_json
        user_settings.save()
        web.grid = default_grid
    return user_settings

@route('/')
def index(web):
    user_settings = load_settings(web)
    
    # Populate the widget library
    library = []
    for name, fn in sorted(widget_types.iteritems()):
        output = fn({'id': 'library-'+name})
        library.append(output)
    
    # Render all the widgets we need
    for row in web.grid:
        for widget_opts in row:
            fn = widget_types.get(widget_opts['type'], render_error)
            widget_opts['output'] = fn(widget_opts)
    template('index.html', {'grid': web.grid, 'library': library})

@route('/ajax/layout')
def ajax_layout(web):
    user_settings = load_settings(web)
    widgets = {}
    for row in web.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    new_grid = []
    row_count = web.input('rows')
    for i in xrange(int(row_count)):
        new_row = []
        for widget_id in web.input('row%s'%i):
            if widget_id in widgets:
                new_row.append(widgets[widget_id])
        new_grid.append(new_row)
    user_settings.grid = simplejson.dumps(new_grid)
    user_settings.save()
    append(simplejson.dumps({}))

@route('/ajax/add')
def ajax_add(web):
    user_settings = load_settings(web)
    # Insert the new widget and set its type up
    print 'Adding at %s,%s'%(web.input('row'), web.input('before'))
    new_widget = add_new_widget(web.grid, int(web.input('row')), web.input('before'))
    new_widget['type'] = web.input('type')
    
    # Save the grid to the DB
    user_settings.grid = simplejson.dumps(web.grid)
    user_settings.save()
    
    # Render the new widget and send to the browser
    output = widget_types.get(new_widget['type'], render_error)(new_widget)
    append(simplejson.dumps({'output': output}))

@route('/ajax/config')
def ajax_config(web):
    user_settings = load_settings(web)
    # Build a lookup dict for the widgets
    widgets = {}
    for row in web.grid:
        for widget in row:
            widgets[widget['id']] = widget
    
    # Set the new options
    changed = set()
    for key, value in web.input().iteritems():
        if key.startswith('input_'):
            _, widget_id, name = key.split('_', 2)
            if widget_id in widgets:
                changed.add(widget_id)
                print 'Setting %s[%s] = %s'%(widget_id, name, value)
                widgets[widget_id][name] = value
    
    # Save the grid to the DB
    user_settings.grid = simplejson.dumps(web.grid)
    user_settings.save()
    
    # Render output
    output = {}
    for widget_id in changed:
        output[widget_id] = widget_types.get(widgets[widget_id]['type'], render_error)(widgets[widget_id])
    append(simplejson.dumps({'output': output}))

@route('/debug/grid')
def debug_grid(web):
    from pprint import pformat
    user_settings = load_settings(web)
    append('<pre>'+pformat(web.grid)+'</pre>')

@route('/favicon.ico')
def favicon(web):
    static_serve(web, 'favicon.ico')

@route('/mock')
def mock(web):
    template('mock.html', {})

application = run()
if __name__ == '__main__':
    werkzeug.run_simple('localhost', 8000, application, use_reloader=True)