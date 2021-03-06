import datetime
import pytz

COMMON_TIMEZONE_CHOICES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
PRETTY_TIMEZONE_CHOICES = []
for tz in pytz.common_timezones:
    now = datetime.datetime.now(pytz.timezone(tz))
    PRETTY_TIMEZONE_CHOICES.append((tz, "(GMT%s) %s" % (now.strftime("%z"), tz)))
    
    
def days_of_week(year, week):
    day = datetime.date(year, 2, 1)
    year, weekBase, dayBase = day.isocalendar()
    day += datetime.timedelta(1 - dayBase + (week - weekBase) * 7)
    delta = datetime.timedelta(1)
    for _ in range(6):
        yield day
        day += delta
    yield day
    
    
def date_range(start_date, end_date):
    """
    Returns a generator of all the days between two date objects.
    
    Results include the start and end dates.
    
    Arguments can be either datetime.datetime or date type objects.
    
    h3. Example usage
    
        >>> import datetime
        >>> import calculate
        >>> dr = calculate.date_range(datetime.date(2009,1,1), datetime.date(2009,1,3))
        >>> dr
        <generator object="object" at="at">
        >>> list(dr)
        [datetime.date(2009, 1, 1), datetime.date(2009, 1, 2), datetime.date(2009, 1, 3)]
        
    """
    # If a datetime object gets passed in,
    # change it to a date so we can do comparisons.
    if isinstance(start_date, datetime.datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime.datetime):
        end_date = end_date.date()
    
    # Verify that the start_date comes after the end_date.
    if start_date > end_date:
        raise ValueError('You provided a start_date that comes after the end_date.')
    
    # Jump forward from the start_date...
    while True:
        yield start_date
        # ... one day at a time ...
        start_date = start_date + datetime.timedelta(days=1)
        # ... until you reach the end date.
        if start_date > end_date:
            break