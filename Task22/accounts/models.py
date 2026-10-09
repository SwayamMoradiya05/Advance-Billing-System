import random
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class DistributorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='distributor_profile')
    phone = models.CharField(max_length=20, help_text="Contact phone number of the distributor.")
    company_name = models.CharField(max_length=255, blank=True, null=True, help_text="Registered wholesale business or trade name.")
    distributor_id = models.CharField(max_length=20, unique=True, db_index=True, help_text="Unique Distributor Tracking Identifier e.g. DIST-8842")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00, help_text="Maximum credit allowance.")
    is_verified = models.BooleanField(default=True, help_text="Distributor verification status.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Distributor Profile"
        verbose_name_plural = "Distributor Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.distributor_id})"


class OTPCode(models.Model):
    email = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        if self.is_used:
            return False
        return timezone.now() <= self.created_at + timedelta(minutes=10)

    @classmethod
    def generate_otp(cls, email):
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        code = f"{random.randint(100000, 999999):06d}"
        return cls.objects.create(email=email, code=code)

    @classmethod
    def validate_otp(cls, email, code):
        otp = cls.objects.filter(email=email, code=code, is_used=False).first()
        if otp and otp.is_valid():
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            return True
        return False

