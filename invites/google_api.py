from urllib2 import Request, HTTPError
from django.utils import simplejson
from social_auth.utils import dsa_urlopen
from urllib import urlencode


class AuthTokenException(Exception):
    pass

def google_contacts(user):
    access_token = user.social_auth.get(provider='google-oauth2').extra_data['access_token']
    data = {'alt': 'json', 'max-results': 200}
    url = 'https://www.google.com/m8/feeds/contacts/default/full'
    headers = {
        'Gdata-version': '3.0',
        'Authorization': 'OAuth %s' % access_token
    }
    request = Request(url + '?' + urlencode(data), headers=headers)
    try:
        content = simplejson.loads(dsa_urlopen(request).read())
    except HTTPError as error:
        raise AuthTokenException(str(error))
        
    contacts = []
    if 'entry' in content['feed']:
        for entry in content['feed']['entry']:
            if not entry['title']['$t'] or not 'gd$email' in entry:
                continue
            contact_pic = None
            for link in entry['link']:
                if link['type'] == 'image/*':
                    contact_pic = '%s?access_token=%s' % (link['href'], access_token)
            contacts.append({
                'full_name': entry['title']['$t'],
                'pic': contact_pic,
                'email': entry['gd$email'][0]['address']
            })
    contacts = sorted(contacts, key=lambda k: k['full_name']) 
    return contacts
    #except (ValueError, KeyError, IOError):
    #    return None