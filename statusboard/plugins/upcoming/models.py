import urllib2
import icalendar
import datetime
from dateutil import rrule, tz
from StringIO import StringIO

from django.db import models
from django.utils.translation import ugettext_lazy as _

from statusboard.plugins import Plugin

class Calendar(models.Model):
    class Meta:
        db_name = 'statusboard_upcoming_calendar'
    url = models.CharField(_('URL'), max_length=256, unique=True)
    ts = models.DateTimeField(_('timestamp'))


class CalendarEvent(models.Model):
    class Meta:
        db_name = 'statusboard_upcoming_calendarevent'
    calendar = models.ForeignKey(Calendar, related_name='events', verbose_name=_('calendar'))
    date = models.DateTimeField(_('date'))
    title = models.CharField(_('title'), max_length=256)


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
            try:
                data['cal'] = Calendar.objects.get(url=opts['url'])
            except Calendar.DoesNotExist:
                pass
            else:
                for event in data['cal'].events.filter(date__gte=datetime.datetime.now()).order_by('date')[:8]:
                    data['events'].append({'title': event.title, 'date': event.date.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())})
        return 'upcoming.html', data
    
    def gather(self, url):
        # Check when we last updated this URL
        cal, created = Calendar.objects.get_or_create(url=url, defaults={'ts': datetime.datetime.now()})
        if not created:
            old_ts = cal.ts
            cal.ts = datetime.datetime.now()
            Calendar.objects(pk=cal.pk).update(ts=cal.ts)
            if old_ts and datetime.datetime.now() - old_ts < datetime.timedelta(hours=1):
                return
        
        # Load the calendar
        data = urllib2.urlopen(url).read()
        data = data.replace('00001231T000000Z', '00011231T000000Z') # datetime doesn't like year=0
        ical = icalendar.Calendar.from_string(data)
        
        # Delete all existing events for this URL
        cal.events.all().delete()
        
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
                        CalendarEvent.objects.create(calendar=cal, date=dt.astimezone(tz.tzutc()), title=vevent['SUMMARY'])
            elif dtstart >= now:
                CalendarEvent.objects.create(calendar=cal, date=dtstart.astimezone(tz.tzutc()), title=vevent['SUMMARY'])
