from django.core.management.base import BaseCommand, CommandError
from holiday_manager.models import NationalHoliday
import requests
from xml.dom.minidom import parseString
import HTMLParser
import re
from datetime import datetime
from django.db import transaction
from icalendar import Calendar, Event

WHEN_REGEX = re.compile(r'When: (.*?)</?br>', re.I)

def parse_when(string):
    matches = WHEN_REGEX.search(string)
    date_str = matches.group(1)
    return datetime.strptime(date_str, '%a %d %b %Y').date()
    

class Command(BaseCommand):
    help = "Create db models for national holidays"
    
    cal_urls = {
        'ita':
            {
                'xml': 'http://www.google.com/calendar/feed/italian%40holiday.calendar.google.com/public/basic',
                'ical': 'http://www.google.com/calendar/ical/italian%40holiday.calendar.google.com/public/basic',
            },
        'gbr':
            {
                'ical': 'http://www.google.com/calendar/ical/uk%40holiday.calendar.google.com/public/basic',
            }
    }

    def handle(self, *args, **options):
        self.get_remote_data()
        
    def get_remote_data(self, format='ical'):
        for country_code, feed_urls in self.cal_urls.items():
            to_save = []
            r = requests.get(feed_urls[format])
            if r.status_code != 200:
                raise Exception("HTTP code %s for url %s" % (r.status_code, feed_urls[format]))
            
            if format == 'ical':
                to_save = self.parse_ical_data(country_code, r.text)
            elif format == 'xml':
                to_save = self.parse_xml_data(country_code, r.text)
            else:
                raise CommandError("Invalid format: %s" % format)
            
            self.save_entities(country_code, to_save)
            
    @transaction.commit_on_success
    def save_entities(self, country_code, to_save):
        current_year = datetime.now().year
        filtered = [item for item in to_save if item.date.year == current_year + 1]
        
        NationalHoliday.objects.bulk_create(filtered)
        self.stdout.write("Successfully imported %s entries for %s \n" % (len(filtered), country_code))
        
    def parse_ical_data(self, country_code, content):
        cal = Calendar.from_ical(content)
        to_save = []
        for component in cal.walk('vevent'):
            attrs = {
                'country_code': country_code,
                'name': component['SUMMARY'],
                'date': component.decoded('DTSTART')
            }
            new_instance = NationalHoliday(**attrs)
            to_save.append(new_instance)
        
        return to_save
    
    def parse_xml_data(self, country_code, content):
        html_parser = HTMLParser.HTMLParser()
        dom = parseString(content)
        to_save = []
        entries = dom.getElementsByTagName('entry')
        for entry in entries:
            date = parse_when(entry.getElementsByTagName('summary')[0].firstChild.nodeValue)
            attrs = {
                'country_code': country_code,
                'name': html_parser.unescape(entry.getElementsByTagName('title')[0].firstChild.nodeValue),
                'date': date
            }
            new_instance = NationalHoliday(**attrs)
            to_save.append(new_instance)
        return to_save
        
        
        