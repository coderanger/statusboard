import random

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

def render_builder(opts):
    data = {
        'label': 'CONT1',
        'progress': random.randint(1, 100),
    }
    return render_template(get_template('widget_builder.html'), **data)

def render_label(opts):
    data = {
        'label': 'FC',
    }
    return render_template(get_template('widget_label.html'), **data)

def hex_random(n):
    byte = lambda: '%02x'%random.randint(0, 255)
    return ''.join(byte() for _ in xrange(n))

@route('/')
def index(web):
    if 'name' not in web.session:
        web.session['name'] = hex_random(6)
        web.session.save()
    grid = [
        [{'type': 'label'}, {'type': 'builder'}, {'type': 'builder'},],
        [{'type': 'label'}, {'type': 'builder'}, {'type': 'builder'},  ],
    ]
    for row in grid:
        for widget_opts in row:
            if widget_opts['type'] == 'label':
                fn = render_label
            elif widget_opts['type'] == 'builder':
                fn = render_builder
            widget_opts['output'] = fn(widget_opts)
    template('index.html', {'grid': grid, 'name': web.session['name']})

@route('/mock')
def mock(web):
    template('mock.html', {})

application = run()
if __name__ == '__main__':
    werkzeug.run_simple('localhost', 8000, application, use_reloader=True)