from django.contrib import admin

# Register your models here.
from .models import Subscription, UserSubscription,SubscriptionPrice

#if you want help_text to appear
#class SubscriptionPrice(admin.StackedInline):

class SubscriptionPrice(admin.TabularInline):
    model = SubscriptionPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0

class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionPrice]
    list_display = ['name','active']
    readonly_fields = ['stripe_id']

admin.site.register(Subscription,SubscriptionAdmin)
admin.site.register(UserSubscription)