import random
from datetime import timedelta
from django.db import models
from django.utils import timezone

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
