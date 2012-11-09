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
    
    def client_details(self, client_id):
        response = self.send_request('get', '%s/clients/%s' % (self.api_base_url, client_id))
        return response.json['data']
        
    def list_cards(self):
        response = self.send_request('get', '%s/payments' % self.api_base_url)
        return response.json
    
    def create_card(self, token, client_id=None):
        data = {'token': token}
        if client_id:
            data['client'] = client_id
        response = self.send_request('post', '%s/payments' % self.api_base_url, data=data)
        return response.json['data']
        
    def remove_card(self, card_id):
        response = self.send_request('delete', '%s/payments/%s' % (self.api_base_url, card_id))
        return response.json
        
    def subscribe(self, **kwargs):
        response = self.send_request('post', '%s/subscriptions' % self.api_base_url, data=kwargs)
        return response.json['data']
        
    def send_request(self, method, url, **kwargs):
        kwargs['auth'] = (self.api_key, '')
        #TODO: the certificate on pymill api seems a bit dodgy! CA check fails       
        kwargs['verify'] = False
        http_method = getattr(requests, method)
        return http_method(url, **kwargs)