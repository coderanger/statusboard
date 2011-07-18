from datetime import timedelta

from celery.schedules import schedule
from celery.utils.timeutils import timedelta_seconds

class tick_schedule(schedule):
    """Celery scheduler that always runs on startup with no delay. Arguments
    are the same as for datetime.timedelta.
    """
    def __init__(self, **kwargs):
        super(tick_schedule, self).__init__(timedelta(**kwargs))
        self.__first_run = True

    def is_due(self, last_run_at):
        # Not threadsafe, but I don't think this needs to be.
        # If I'm wrong, throw a mutex around this.
        if self.__first_run:
            self.__first_run = False
            return True, timedelta_seconds(self.run_every)
        return super(tick_schedule, self).is_due(last_run_at)
