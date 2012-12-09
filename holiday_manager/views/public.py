from django.shortcuts import render
from django.core.urlresolvers import reverse
from paypal.standard.forms import PayPalPaymentsForm

def home(request):
    return render(request, 'public/home.html')

def subscribe(request):
    paypal_dict = {
        "cmd": "_xclick-subscriptions",
        "business": "h1_1352217439_biz@gmail.com",
        "a3": "9.99",                      # monthly price 
        "p3": 1,                           # duration of each unit (depends on unit)
        "t3": "M",                         # duration unit ("M for Month")
        "src": "1",                        # make payments recur
        "sra": "1",                        # reattempt payment on payment error
        "no_note": "1",                    # remove extra notes (optional)
        "item_name": "Holiday manager subscription",
        "notify_url": request.build_absolute_uri(reverse('paypal:paypal-ipn')),
        "return_url": request.build_absolute_uri(reverse('home')),
        "cancel_return": request.build_absolute_uri(reverse('home')),
        'custom': 'some custom data'
    }
    
    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict, button_type="subscribe")
    return render(request, 'holiday_manager/public/subscribe.html', {'paypal_form': form})