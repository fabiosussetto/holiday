import requests

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
    api_base_url = 'https://www.googleapis.com/calendar/v3/users/me'
    
    def __init__(self, api_key=None, access_token=None):
        self.access_token = access_token
        self.api_key = api_key
        
    def list_calendars(self):
        response = self.send_request('get', '/calendarList')
        return response.json['items']        
        
    def send_request(self, method, url, **kwargs):
        auth_params = {'key': self.api_key}
        if self.access_token:
            kwargs['headers'] = {'Authorization': 'OAuth %s' % self.access_token}
            
        if not 'params' in kwargs:
            kwargs['params'] = auth_params
        else:
            kwargs['params'].update(auth_params)
            
        http_method = getattr(requests, method)
        return http_method(self.api_base_url + url, **kwargs)