from urllib2 import Request, HTTPError
from django.utils import simplejson
from social_auth.utils import dsa_urlopen
from urllib import urlencode
from holiday_manager.utils import refresh_token


class AuthTokenException(Exception):
    pass

def google_contacts(user):
    social_auth = user.social_auth.get(provider='google-oauth2')
    
    def _req(access_token):
        data = {'alt': 'json', 'max-results': 200}
        url = 'https://www.google.com/m8/feeds/contacts/default/full'
        headers = {
            'Gdata-version': '3.0',
            'Authorization': 'OAuth %s' % access_token
        }
        request = Request(url + '?' + urlencode(data), headers=headers)
        return simplejson.loads(dsa_urlopen(request).read())
        
    try:
        access_token = social_auth.extra_data['access_token']
        content = _req(access_token)
    except HTTPError as error:
        updated_social_auth = refresh_token(social_auth)
        access_token = updated_social_auth.extra_data['access_token']
        content = _req(access_token)
        #raise AuthTokenException(str(error))
        
    contacts = []
    if 'entry' in content['feed']:
        for entry in content['feed']['entry']:
            if not entry['title']['$t'] or not 'gd$email' in entry:
                continue
            contact_pic = None
            for link in entry['link']:
                if link['type'] == 'image/*' and 'gd$etag' in link:
                    contact_pic = '%s?access_token=%s' % (link['href'], access_token)
                    
            first_name = last_name = None
            try:
                first_name = entry['gd$name']['gd$givenName']['$t']
                last_name = entry['gd$name']['gd$familyName']['$t']
            except KeyError:
                pass
            contacts.append({
                'full_name': entry['title']['$t'],
                'first_name': first_name,
                'last_name': last_name,
                'pic': contact_pic,
                'email': entry['gd$email'][0]['address']
            })
    contacts = sorted(contacts, key=lambda k: k['full_name']) 
    return contacts
