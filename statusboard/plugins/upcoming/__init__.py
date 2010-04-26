import urllib2
import icalendar
import datetime
from dateutil import rrule, tz
from StringIO import StringIO
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
            for event in CalendarEvent.find().filter_by(url=opts['url']).filter(CalendarEvent.date>datetime.datetime.now()).order_by(CalendarEvent.date)[:8]:
                data['events'].append({'title': event.title, 'date': event.date.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())})
        return 'upcoming.html', data
    
    def gather(self, url):
        # Check when we last updated this URL
        cal = Calendar.find().filter_by(url=url).first()
        if cal and cal.ts and datetime.datetime.now() - cal.ts < datetime.timedelta(hours=1):
            return
            #pass
        
        # Load the calendar
        data = urllib2.urlopen(url).read()
        data = data.replace('00001231T000000Z', '00011231T000000Z') # datetime doesn't like year=0
        ical = icalendar.Calendar.from_string(data)
        
        # Delete all existing events for this URL
        CalendarEvent.find().filter_by(url=url).delete()
        
        # Create the Calendar if needed
        if not cal:
            cal = Calendar(url=url).add()
        cal.ts = datetime.datetime.now()
        
        # Get the timezone for this calendar
        now = datetime.datetime.now(tz.tzlocal())
        for vtimezone in ical.walk('VTIMEZONE'):
            sio = StringIO()
            for line in str(vtimezone).splitlines():
                if not line.lower().startswith('x-'):
                    sio.write(line)
                    sio.write('\r\n')
            sio.seek(0)
            cal_tz = tz.tzical(sio).get()
            break
        else:
            cal_tz = tz.tzutc()
        
        # Add new events
        for vevent in ical.walk('VEVENT'):
            dtstart = vevent['DTSTART'].dt
            if not isinstance(dtstart, datetime.datetime):
                dtstart = datetime.datetime.combine(dtstart, datetime.time(0))
            if dtstart.tzinfo is None:
                dtstart = dtstart.replace(tzinfo=cal_tz)
            
            if 'RRULE' in vevent:
                recur = rrule.rrulestr(str(vevent['RRULE']), dtstart=dtstart)
                for dt in recur[:20]:
                    print dt
                    if dt >= now:
                        CalendarEvent(url=url, date=dt.astimezone(tz.tzutc()), title=vevent['SUMMARY']).add()
            elif dtstart >= now:
                CalendarEvent(url=url, date=dtstart.astimezone(tz.tzutc()), title=vevent['SUMMARY']).add()
        session().commit()