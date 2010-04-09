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

from utils import hex_random
     
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
        'label': 'CONT1',
        'progress': random.randint(1, 100),
    }
    return render_template(get_template('widget_builder.html'), **data)

def render_label(opts):
    data = {
        'id': opts['id'],
        'label': 'FC',
    }
    return render_template(get_template('widget_label.html'), **data)

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
    for row in web.grid:
        for widget_opts in row:
            if widget_opts['type'] == 'label':
                fn = render_label
            elif widget_opts['type'] == 'builder':
                fn = render_builder
            widget_opts['output'] = fn(widget_opts)
    template('index.html', {'grid': web.grid})

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

@route('/mock')
def mock(web):
    template('mock.html', {})

application = run()
if __name__ == '__main__':
    werkzeug.run_simple('localhost', 8000, application, use_reloader=True)