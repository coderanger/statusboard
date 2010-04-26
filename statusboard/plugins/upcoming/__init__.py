import urllib2
import icalendar
import datetime
from juno import *
from statusboard.plugins import Plugin

Calendar = model('Calendar',
    url='string',
    ts='datetime',
)

CalendarEvent = model('CalendarEvent',
    url='string',
    date='datetime',
    title='string',
)

class Upcoming(Plugin):
    def css(self):
        yield 'upcoming.css'
    
    def js(self):
        yield 'upcoming.js'
    
    def render(self, opts):
        data = {
            'id': opts['id'],
            'url': opts.get('url', ''),
            'cal': None,
            'events': [],
        }
        if opts.get('url'):
            self.gather_request(opts['url'], run_for=3600*24)
            data['cal'] = Calendar.find().filter_by(url=opts['url']).first()
            data['events'] = CalendarEvent.find().filter_by(url=opts['url']).all()
        return 'upcoming.html', data
    
    def gather(self, url):
        # Check when we last updated this URL
        cal = Calendar.find().filter_by(url=url).first()
        if cal and cal.ts and datetime.datetime.now() - cal.ts < datetime.timedelta(hours=1):
            return
        
        # Load the calendar
        data = urllib2.urlopen(url).read()
        ical = icalendar.Calendar.from_string(data)
        
        # Delete all existing events for this URL
        CalendarEvent.find().filter_by(url=url).delete()
        
        # Add new events
        if not cal:
            cal = Calendar(url=url).add()
        cal.ts = datetime.datetime.now()
        for vevent in ical.walk('VEVENT'):
            CalendarEvent(url=url, date=vevent['DTSTART'].dt, title=vevent['SUMMARY']).add()
        session().commit()