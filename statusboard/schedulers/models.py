from datetime import datetime, timedelta

from celery import schedules
from celery.utils.timeutils import timedelta_seconds

from sqlalchemy import Column, Integer, String, Text, DateTime, \
        Sequence, Boolean, ForeignKey, SmallInteger
from sqlalchemy.orm import relation, sessionmaker
from sqlalchemy.orm.interfaces import MapperExtension
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData

metadata = MetaData()
ModelBase = declarative_base(metadata=metadata)


class IntervalSchedule(ModelBase):
    __tablename__ = 'statusboard_intervalschedule'
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('intervalschedule_id_sequence'), primary_key=True,
                      autoincrement=True)
    every    = Column(Integer)
    period   = Column(String(24))

    def __init__(self, every, period='seconds'):
        self.every = every
        self.period = period

    @property
    def schedule(self):
        return schedules.schedule(timedelta(**{self.period: self.every}))

    @classmethod
    def from_schedule(cls, schedule):
        return cls(every=timedelta_seconds(schedule.run_every),
                   period="seconds")

    def __str__(self):
        if self.every == 1:
            return 'every %s' % self.period[:-1]
        return 'every %s %s' % (self.every, self.period)


class CrontabSchedule(ModelBase):
    __tablename__ = 'statusboard_crontabschedule'
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('crontabschedule_id_sequence'), primary_key=True,
                      autoincrement=True)
    minute = Column(String(64), default='*')                    
    hour = Column(String(64), default='*')
    day_of_week = Column(String(64), default='*')

    def __init__(self, minute='*', hour='*', day_of_week='*'):
        self.minute = minute
        self.hour = hour
        self.day_of_week = day_of_week

    @property
    def schedule(self):
        return schedules.crontab(minute=self.minute,
                                hour=self.hour,
                                day_of_week=self.day_of_week)

    @classmethod
    def from_schedule(cls, schedule):
        return cls(minute=schedule._orig_minute,
                   hour=schedule._orig_hour,
                   day_of_week=schedule._orig_day_of_week)

    def __str__(self):
        rfield = lambda f: f and str(f).replace(" ", "") or "*"
        return '%s %s %s (m/h/d)' % (rfield(self.minute),
                                      rfield(self.hour),
                                      rfield(self.day_of_week))


class PeriodicTasks(ModelBase):
    __tablename__ = 'statusboard_periodictasks'
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('periodictasks_id_sequence'), primary_key=True,
                    autoincrement=True)
    last_update = Column(DateTime, nullable=False)

    @classmethod
    def last_change(cls, session):
        obj = session.query(cls).get(1)
        if obj:
            # Make sure it isn't cached next time
            session.expire(obj)
            return obj.last_update


class _TaskUpdateExtension(MapperExtension):
    def after_update(self, mapper, connection, instance):
        session = sessionmaker(bind=connection)()
        obj = session.query(PeriodicTasks).get(1)
        if not obj:
            obj = PeriodicTasks(id=1)
            session.add(obj)
        obj.last_update = datetime.now()
        session.commit()
    
    after_insert = after_update
    after_delete = after_update


class PeriodicTask(ModelBase):
    __tablename__ = 'statusboard_periodictask'
    __table_args__ = {"sqlite_autoincrement": True}

    id       = Column(Integer, Sequence('periodictask_id_sequence'), primary_key=True,
                    autoincrement=True)
    name = Column(String(200), unique=True, nullable=False)
    task = Column(String(200), nullable=False)
    interval_id = Column(Integer, ForeignKey('statusboard_intervalschedule.id'))
    intevral = relation(IntervalSchedule)
    crontab_id = Column(Integer, ForeignKey('statusboard_crontabschedule.id'))
    crontab = relation(CrontabSchedule)
    args = Column(Text, default='[]', nullable=False)
    kwargs = Column(Text, default='{}', nullable=False)
    queue = Column(String(200), default=None)
    exchange = Column(String(200), default=None)
    routing_key = Column(String(200), default=None)
    expires = Column(DateTime)
    enabled = Column(Boolean, default=False, nullable=False)
    last_run_at = Column(DateTime)
    total_run_count = Column(Integer, default=0, nullable=False)
    date_changed = Column(DateTime, default=datetime.now, nullable=False)
    
    no_changes = False
    
    __mapper_args__ = {
        'extension': _TaskUpdateExtension(),
    }
    
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def schedule(self):
        if self.interval_id:
            return self.interval.schedule
        if self.crontab_id:
            return self.crontab.schedule

    def __str__(self):
        if self.interval:
            return '%s: %s' % (self.name, self.interval)
        if self.crontab:
            return '%s: %s' % (self.name, self.crontab)
        return '%s: {no schedule}' % (self.name, )

# class Message(ModelBase):
#     __tablename__ = 'kombu_message'
#     __table_args__ = {"sqlite_autoincrement": True}
# 
#     id       = Column(Integer, Sequence('message_id_sequence'), primary_key=True,
#                       autoincrement=True)
#     visible  = Column(Boolean, default=True, index=True)
#     sent_at  = Column('timestamp', DateTime, nullable=True, index=True,
#                       onupdate = datetime.datetime.now)
#     payload  = Column(Text, nullable=False)
#     queue_id = Column(SmallInteger, ForeignKey('kombu_queue.id', name='FK_kombu_message_queue'))
#     version  = Column(SmallInteger, nullable=False, default=1)
# 
#     __mapper_args__ = {'version_id_col': version}
# 
#     def __init__(self, payload, queue):
#         self.payload  = payload
#         self.queue = queue
    # 
    # def __str__(self):
    #     return "<Message(%s, %s, %s, %s)>" % (self.visible, self.sent_at, self.payload, self.queue_id)

