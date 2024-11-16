from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionPrice
import helpers.billing
from django.urls import reverse
from django.conf import settings

BASE_URL = settings.BASE_URL

# Create your views here.
def product_price_redirect_view(request,price_id=None,*args,**kwargs):
    request.session['checkout_subscription_price_id'] = price_id
    return redirect('stripe-checkout-start')

@login_required
def checkout_redirect_view(request):
    
    checkout_subscription_price_id = request.session.get('checkout_subscription_price_id')
    
    try:
        obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
    except:
        obj=None
    if checkout_subscription_price_id is None or obj is None:
        redirect('pricing')

    customer_stripe_id = request.user.customer.stripe_id
    success_path_url = reverse('stripe-checkout-end')
    success_url = BASE_URL + success_path_url

    pricing_path_url = reverse('pricing')
    cancel_url = BASE_URL + pricing_path_url

    price_stripe_id = obj.stripe_id

    url = helpers.billing.start_checkout_session(
        customer_stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        price_stripe_id=price_stripe_id,
        raw=False
    )
    return redirect(url)

def checkout_finalize_view(request):
    session_id = request.session.get('session_id')
    checkout_r = helpers.billing.get_checkout_session(session_id,raw=True)
    customer_id = checkout_r.customer
    sub_stripe_id = checkout_r.subscription
    sub_r = helpers.billing.get_subscription(sub_stripe_id,raw=True)
    sub_plan = sub_r.plan
    sub_plan_price_stripe_id = sub_plan.id
    
    context = {
        "subscription" : sub_r,
        "checkout" : checkout_r,
    }
    return render(request,"checkout/success.hmtl",context)

