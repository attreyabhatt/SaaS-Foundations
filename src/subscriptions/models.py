from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save
import helpers.billing
from django.urls import reverse

User = settings.AUTH_USER_MODEL #"auth.User"
ALLOW_CUSTOM_GROUPS = True

SUBSCRIPTION_PERMISSIONS = [
    ("advanced", "Advanced Perm"), # subscriptions.advanced
    ("pro", "Pro Perm"),  # subscriptions.pro
    ("basic", "Basic Perm"),  # subscriptions.basic,
    ("ai", "AI Perm")
]

# Create your models here.
class Subscription(models.Model):
    """
    Subscription Plan = Stripe Product
    """
    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True,null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions =  models.ManyToManyField(Permission, limit_choices_to={
        "content_type__app_label": "subscriptions", "codename__in": [x[0]for x in SUBSCRIPTION_PERMISSIONS]
        }
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    order = models.IntegerField(default=-1,help_text='Ordering on Django Pricing Page')
    featured = models.BooleanField(default=True,help_text='Featured on Django Pricing Page')
    updated = models.DateTimeField(auto_now=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
    features = models.TextField(help_text="Features for pricing, seperated by new line", blank=True, null=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        permissions = SUBSCRIPTION_PERMISSIONS
        ordering = ['order','featured','-updated']

    def get_features_as_list(self):
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n")]

    def save(self, *args, **kwargs):

        #if the stipe id doesn't exist already 
        # and the email is confirmed

        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                name=self.name,
                metadata={ "subscription_plan_id": self.id},
                raw=False
                )                    
            self.stripe_id = stripe_id
        super().save(*args, **kwargs) 
     

class SubscriptionPrice(models.Model):
    """
    Subscription Price = Stripe Price
    """

    class IntervalChoices(models.TextChoices):
        MONTHLY = "month","Monthly"
        YEARLY = "year","Yearly"

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL,null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(max_length=120,
                                default=IntervalChoices.MONTHLY,
                                choices=IntervalChoices.choices) # get_<field_name>_display
    price = models.DecimalField(max_digits=10,decimal_places=2,default=99.99)
    order = models.IntegerField(default=-1,help_text='Ordering on Django Pricing Page')
    featured = models.BooleanField(default=True,help_text='Featured on Django Pricing Page')
    updated = models.DateTimeField(auto_now=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subscription__order','order','featured','-updated']

    def get_checkout_url(self):
        return reverse("sub-price-checkout",kwargs={"price_id":self.id})

    @property
    def display_features_list(self):
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()

    @property
    def display_sub_name(self):
        if not self.subscription.name:
            return "Plan"
        return self.subscription.name

    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle
        
    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id

    @property
    def stripe_price(self):
        """
        remove decimal places
        """
        return int(self.price * 100)

    @property
    def stripe_currency(self):
        return "usd"

    def save(self,*args, **kwargs):
        if (not self.stripe_id and self.product_stripe_id is not None):
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={
                        "subscription_plan_price_id": self.id
                },
                raw=False,
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)
        if self.featured and self.subscription:
            qs = SubscriptionPrice.objects.filter(
                subscription=self.subscription,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)

class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        TRIALING = 'trialing', 'Trialing'
        INCOMPLETE = 'incomplete', 'Incomplete'
        INCOMPLETE_EXPIRED = 'incomplete_expired', 'Incomplete Expired'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELED = 'canceled', 'Canceled'
        UNPAID = 'unpaid', 'Unpaid'
        PAUSED = 'paused', 'Paused'

class UserSubscription(models.Model):
    # cascade - when the user is deleted their Subscriptions (UserSubscriptions) are deleted as well
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)

    # a user doesn't need to have a subscription 
    subscription = models.ForeignKey(Subscription, 
    on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    
    original_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_end = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
        
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def billing_cycle_anchor(self):
        """
        https://docs.stripe.com/payments/checkout/billing-cycle
        Optional delay to start new subscription in
        Stripe checkout
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())

    def save(self, *args, **kwargs):
        if (self.original_period_start is None and
            self.current_period_start is not None
            ):
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)



def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list("groups__id", flat=True)
        subs_groups_set = set(subs_groups)
        # groups_ids = groups.values_list('id', flat=True) # [1, 2, 3] 
        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_set
        final_group_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_group_ids)


post_save.connect(user_sub_post_save, sender=UserSubscription)