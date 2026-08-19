from django.db import models
from django.contrib.auth.models import User

class DistributorProfile(models.Model):
    """
    Distributor profile extending Django's built-in User model.
    Stores additional wholesale business information such as phone number,
    company name, and credit allocation limits.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='distributor_profile')
    phone = models.CharField(max_length=20, help_text="Contact phone number of the distributor.")
    company_name = models.CharField(max_length=255, blank=True, null=True, help_text="Registered wholesale business or trade name.")
    distributor_id = models.CharField(max_length=20, unique=True, db_index=True, help_text="Unique Distributor Tracking Identifier e.g. DIST-8842")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00, help_text="Maximum credit allowance in USD/INR.")
    is_verified = models.BooleanField(default=True, help_text="Distributor verification status.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Distributor Profile"
        verbose_name_plural = "Distributor Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.distributor_id})"
