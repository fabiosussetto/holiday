import requests
import json
from holiday_manager.utils import refresh_token

def calendar_choices(data):
    choices = []
    for item in data:
        try:
            choices.append((item['id'], item['summary']))
        except KeyError:
            continue
    return choices
    

class GoogleCalendarApi(object):
    access_token = None
    api_key = None
    api_base_url = 'https://www.googleapis.com/calendar/v3'
    
    def __init__(self, api_key=None, access_token=None, auth_user=None):
        self.access_token = access_token
        self.api_key = api_key
        self.auth_user = auth_user
        
    def list_calendars(self):
        response = self.send_request('get', '/users/me/calendarList')
        return response.json['items']
        
    def create_event(self, calendar_id, start=None, end=None, summary=None):
        data = {
            'start': {
                'date': start.isoformat()
            },
            'end': {
                'date': end.isoformat()
            },
            'summary': summary
        }
        response = self.send_request('post', '/calendars/%s/events' % calendar_id, data=json.dumps(data))
        response.raise_for_status()
        return response.json
        
    def send_request(self, method, url, **kwargs):
        def _req(access_token):
            auth_params = {'key': self.api_key}
            if self.access_token:
                kwargs['headers'] = {
                    'Authorization': 'OAuth %s' % access_token,
                    'Content-Type': 'application/json'
                }
                
            if not 'params' in kwargs:
                kwargs['params'] = auth_params
            else:
                kwargs['params'].update(auth_params)
                
            http_method = getattr(requests, method)
            return http_method(self.api_base_url + url, **kwargs)
        
        resp = _req(self.access_token)
        if resp.status_code == 401:
            updated_data = refresh_token(self.auth_user)
            resp = _req(updated_data.extra_data['access_token'])
            
        return resp