import requests

class PayMillApi(object):
    api_key = None
    api_base_url = 'https://api.paymill.de/v2'
    
    def __init__(self, api_key):
        self.api_key = api_key
        
    def create_client(self, email=None, description=None):
        data = {
            'email': email,
            'description': description
        }
        response = self.send_request('post', '%s/clients' % self.api_base_url, data=data)
        return response.json['data']
    
    def list_cards(self, client_id):
        query = {'client': client_id}
        response = self.send_request('get', '%s/payments' % self.api_base_url, params=query)
        return response.json
    
    def create_card(self, token, client_id=None):
        data = {'token': token}
        if client_id:
            data['client_id'] = client_id
        response = self.send_request('post', '%s/payments' % self.api_base_url, data=data)
        return response.json['data']
        
    def send_request(self, method, url, **kwargs):
        kwargs['auth'] = (self.api_key, '')
        #TODO: the certificate on pymill api seems a bit dodgy! CA check fails       
        kwargs['verify'] = False
        http_method = getattr(requests, method)
        return http_method(url, **kwargs)