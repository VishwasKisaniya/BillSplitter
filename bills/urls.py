from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Group URLs
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    
    # Bill URLs
    path('bills/create/', views.create_bill, name='create_bill'),
    path('bills/create/<int:group_id>/', views.create_bill, name='create_bill_group'),
    path('bills/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bills/<int:bill_id>/split/', views.create_bill_split, name='create_bill_split'),
    
    # Payment URLs
    path('pay/<int:split_id>/', views.pay_bill, name='pay_bill'),
    path('payment-redirect/<int:payment_id>/', views.payment_redirect, name='payment_redirect'),
] 