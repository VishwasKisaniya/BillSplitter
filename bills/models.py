from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, unique=True)
    upi_id = models.CharField(max_length=50, blank=True, null=True, help_text="UPI ID for payments")
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='bill_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Bill(models.Model):
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_bills')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='bills')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount}"

class BillSplit(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bill_splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} owes {self.amount} for {self.bill.title}"
    
    def mark_as_paid(self):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.save()

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('AMAZON', 'Amazon Pay'),
        ('GPAY', 'Google Pay'),
        ('PAYTM', 'Paytm'),
        ('UPI', 'UPI Payment'),
        ('OTHER', 'Other')
    )
    
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_made')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_split = models.ForeignKey(BillSplit, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='UPI')
    upi_id = models.CharField(max_length=50, blank=True, null=True, help_text="UPI ID used for payment")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.payer.username} paid {self.amount} to {self.recipient.username}"
