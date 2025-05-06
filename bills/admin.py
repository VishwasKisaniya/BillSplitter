from django.contrib import admin
from .models import Profile, Group, Bill, BillSplit, Payment

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'created_by__username')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'created_by', 'group', 'created_at')
    list_filter = ('created_at', 'group')
    search_fields = ('title', 'description', 'created_by__username')

@admin.register(BillSplit)
class BillSplitAdmin(admin.ModelAdmin):
    list_display = ('bill', 'user', 'amount', 'is_paid')
    list_filter = ('is_paid', 'paid_at')
    search_fields = ('bill__title', 'user__username')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payer', 'recipient', 'amount', 'payment_method', 'created_at')
    list_filter = ('payment_method', 'created_at')
    search_fields = ('payer__username', 'recipient__username')
