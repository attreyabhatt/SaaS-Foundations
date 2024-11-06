from django.db import models
from django.conf import settings
import helpers.billing

from allauth.account.signals import (
    user_signed_up as allauth_user_signed_up,
    email_confirmed as allauth_email_confirmed
)

User = settings.AUTH_USER_MODEL ##auth.user
# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    #customerid
    stripe_id = models.CharField(max_length=120,null=True,blank=True)
    #initial email
    init_email = models.EmailField(blank=True,null=True)
    init_email_confirmed = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.user.username}"

    # obj.save() method is used to store things in database
    # so whenever a new customer is saved db this save() will trigger
    #overrriding the save method of django to do somethings pre-save
    def save(self, *args, **kwargs):

        #if the stipe id doesn't exist already 
        # and the email is confirmed

        if not self.stripe_id:
            if self.init_email_confirmed and self.init_email:
                email  = self.init_email

                # if email isn't empty
                if email != "" or email is not None:
                    stripe_id = helpers.billing.create_customer(email=email,metadata={
                        "user_id": self.user.id, 
                        "username": self.user.username
                    }, raw=False)                    
                    self.stripe_id = stripe_id

        super().save(*args, **kwargs)
        #anything after super is post save it will not update though
    
def allauth_user_signed_up_handler(request, user, *args, **kwargs):
    email = user.email
    Customer.objects.create(
        user=user,
        init_email=email,
        init_email_confirmed=False,
    )

allauth_user_signed_up.connect(allauth_user_signed_up_handler)

def allauth_email_confirmed_handler(request, email_address, *args, **kwargs):
    qs = Customer.objects.filter(
        init_email=email_address,
        init_email_confirmed=False,
    )
    # does not send the save method or create the
    # stripe customer
    # qs.update(init_email_confirmed=True)
    for obj in qs:
        obj.init_email_confirmed=True
        # send the signal
        obj.save()


allauth_email_confirmed.connect(allauth_email_confirmed_handler)

