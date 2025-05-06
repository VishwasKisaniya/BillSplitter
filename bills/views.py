from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
from urllib.parse import quote
import qrcode
import io
import base64
from django.http import HttpResponse

from .models import Profile, Group, Bill, BillSplit, Payment
from .forms import (
    UserRegistrationForm, ProfileUpdateForm, GroupForm,
    AddMemberForm, BillForm, BillSplitForm, PaymentForm
)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'bills/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    groups = user.bill_groups.all()
    
    # Get bills where the user owes money
    bills_to_pay = BillSplit.objects.filter(
        user=user,
        is_paid=False
    ).select_related('bill')
    
    # Get bills where the user is owed money
    bills_to_receive = BillSplit.objects.filter(
        bill__created_by=user,
        is_paid=False
    ).exclude(user=user)
    
    # Calculate net balances with other users
    # Positive means user is owed money, negative means user owes money
    balances = {}
    
    # Money user owes to others
    owed = BillSplit.objects.filter(
        user=user,
        is_paid=False
    ).values('bill__created_by').annotate(
        total=Sum('amount')
    )
    
    for item in owed:
        other_user = User.objects.get(id=item['bill__created_by'])
        if other_user not in balances:
            balances[other_user] = Decimal(0)
        balances[other_user] -= item['total']
    
    # Money others owe to user
    owed_to_me = BillSplit.objects.filter(
        bill__created_by=user,
        is_paid=False
    ).exclude(
        user=user
    ).values('user').annotate(
        total=Sum('amount')
    )
    
    for item in owed_to_me:
        other_user = User.objects.get(id=item['user'])
        if other_user not in balances:
            balances[other_user] = Decimal(0)
        balances[other_user] += item['total']
    
    context = {
        'groups': groups,
        'bills_to_pay': bills_to_pay,
        'bills_to_receive': bills_to_receive,
        'balances': balances.items()
    }
    
    return render(request, 'bills/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'bills/profile.html', {'form': form})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            group.members.add(request.user)
            messages.success(request, f'Group "{group.name}" has been created!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupForm()
    
    return render(request, 'bills/create_group.html', {'form': form})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    bills = Bill.objects.filter(group=group).order_by('-created_at')
    
    # Check if user is a member of the group
    if request.user not in group.members.all():
        messages.error(request, 'You are not a member of this group.')
        return redirect('dashboard')
    
    # Add member form
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data.get('phone_number')
            try:
                profile = Profile.objects.get(phone_number=phone_number)
                if profile.user in group.members.all():
                    messages.warning(request, f'{profile.user.username} is already a member of this group.')
                else:
                    group.members.add(profile.user)
                    messages.success(request, f'{profile.user.username} has been added to the group.')
            except Profile.DoesNotExist:
                messages.error(request, f'No user found with phone number {phone_number}.')
            return redirect('group_detail', group_id=group.id)
    else:
        form = AddMemberForm()
    
    context = {
        'group': group,
        'bills': bills,
        'form': form,
    }
    return render(request, 'bills/group_detail.html', context)

@login_required
def create_bill(request, group_id=None):
    group = None
    if group_id:
        group = get_object_or_404(Group, id=group_id)
        # Check if user is a member of the group
        if request.user not in group.members.all():
            messages.error(request, 'You are not a member of this group.')
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.created_by = request.user
            bill.save()
            
            # Redirect to the bill split page
            return redirect('create_bill_split', bill_id=bill.id)
    else:
        initial = {}
        if group:
            initial['group'] = group
        form = BillForm(initial=initial)
        
        # Limit group choices to the groups the user is a member of
        form.fields['group'].queryset = request.user.bill_groups.all()
    
    return render(request, 'bills/create_bill.html', {'form': form})

@login_required
def create_bill_split(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    group = bill.group
    
    # Check if user created the bill
    if bill.created_by != request.user:
        messages.error(request, 'You can only split bills that you have created.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BillSplitForm(request.POST, group=group)
        if form.is_valid():
            split_type = form.cleaned_data['split_type']
            
            # Get selected members
            selected_members = []
            for member in group.members.all():
                if form.cleaned_data.get(f'member_{member.id}', False):
                    selected_members.append(member)
            
            if not selected_members:
                messages.error(request, 'You must select at least one member to split the bill with.')
                return redirect('create_bill_split', bill_id=bill.id)
            
            with transaction.atomic():
                # Delete any existing splits for this bill
                BillSplit.objects.filter(bill=bill).delete()
                
                if split_type == 'equal':
                    # Calculate equal amount
                    amount_per_person = bill.amount / len(selected_members)
                    
                    # Create bill splits
                    for member in selected_members:
                        BillSplit.objects.create(
                            bill=bill,
                            user=member,
                            amount=amount_per_person
                        )
                else:  # custom split
                    total = Decimal(0)
                    
                    # Create bill splits with custom amounts
                    for member in selected_members:
                        amount = form.cleaned_data.get(f'amount_{member.id}')
                        if amount:
                            BillSplit.objects.create(
                                bill=bill,
                                user=member,
                                amount=amount
                            )
                            total += amount
                    
                    # Check if total matches bill amount
                    if total != bill.amount:
                        messages.warning(request, 
                                         f'The total split amount (${total}) does not match the bill amount (${bill.amount}). ' +
                                         'The bill has been split based on the amounts you provided.')
            
            messages.success(request, 'Bill has been successfully split!')
            return redirect('bill_detail', bill_id=bill.id)
    else:
        form = BillSplitForm(group=group)
    
    return render(request, 'bills/create_bill_split.html', {
        'form': form,
        'bill': bill,
        'group': group
    })

@login_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    group = bill.group
    splits = bill.splits.all().select_related('user')
    
    # Check if user is a member of the group
    if request.user not in group.members.all():
        messages.error(request, 'You are not a member of this group.')
        return redirect('dashboard')
    
    context = {
        'bill': bill,
        'group': group,
        'splits': splits,
    }
    return render(request, 'bills/bill_detail.html', context)

@login_required
def pay_bill(request, split_id):
    bill_split = get_object_or_404(BillSplit, id=split_id)
    
    # Check if user is the one who needs to pay
    if bill_split.user != request.user:
        messages.error(request, 'You can only pay your own bills.')
        return redirect('dashboard')
    
    # Check if bill creator is the same as the payer (user shouldn't pay themselves)
    if bill_split.bill.created_by == request.user:
        messages.error(request, 'You cannot pay yourself for a bill you created.')
        return redirect('dashboard')
    
    # Get recipient's UPI ID from their profile
    recipient = bill_split.bill.created_by
    recipient_upi_id = recipient.profile.upi_id if hasattr(recipient, 'profile') else None
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            
            # Use recipient's UPI ID for payment
            upi_id = recipient_upi_id
            
            # Create a payment record
            payment = Payment.objects.create(
                payer=request.user,
                recipient=recipient,
                amount=bill_split.amount,
                bill_split=bill_split,
                payment_method=payment_method,
                upi_id=upi_id if payment_method == 'UPI' else None
            )
            
            # Mark the bill split as paid
            bill_split.mark_as_paid()
            
            messages.success(request, f'Payment for {bill_split.bill.title} initiated!')
            
            # Pass payment info to redirect view
            return redirect('payment_redirect', payment_id=payment.id)
    else:
        form = PaymentForm(user=request.user, initial={'amount': bill_split.amount})
    
    context = {
        'form': form,
        'bill_split': bill_split,
        'recipient_upi_id': recipient_upi_id
    }
    return render(request, 'bills/pay_bill.html', context)

@login_required
def payment_redirect(request, payment_id):
    # Get payment info
    payment = get_object_or_404(Payment, id=payment_id)
    bill_split = payment.bill_split
    
    # Create payment links based on payment method
    payment_urls = {
        'AMAZON': 'https://www.amazon.in/amazonpay/home',
        'GPAY': 'https://pay.google.com',
        'PAYTM': 'https://paytm.com',
        'OTHER': 'dashboard',
    }
    
    # Generate UPI payment link if UPI payment method is selected
    if payment.payment_method == 'UPI' and payment.upi_id:
        # Format the payment details
        bill_title = quote(f"Payment for {bill_split.bill.title}")
        pa = quote(payment.upi_id)
        pn = quote(payment.recipient.username)
        am = payment.amount
        
        # Create multiple UPI deep link formats for better compatibility
        upi_links = {
            'standard': f"upi://pay?pa={pa}&pn={pn}&am={am}&cu=INR&tn={bill_title}",
            'gpay': f"https://pay.google.com/gp/v/save/{pa}?pa={pa}&pn={pn}&am={am}&cu=INR&tn={bill_title}",
            'phonepe': f"phonepe://pay?pa={pa}&pn={pn}&am={am}&cu=INR&tn={bill_title}",
            'paytm': f"paytm://pay?pa={pa}&pn={pn}&am={am}&cu=INR&tn={bill_title}"
        }
        
        # Generate QR code for UPI payment
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_links['standard'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Check if request is likely from a mobile device using User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(x in user_agent for x in ['android', 'iphone', 'mobile', 'mobi'])
        
        if is_mobile:
            # On mobile, use native UPI app link
            payment_url = upi_links['standard']
            fallback_url = upi_links['gpay']
        else:
            # On desktop, prefer web-based options
            payment_url = upi_links['gpay']  # Web GPay as primary for desktop
            fallback_url = upi_links['standard'] 
    else:
        payment_url = payment_urls.get(payment.payment_method, 'dashboard')
        fallback_url = None
        upi_links = None
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(x in user_agent for x in ['android', 'iphone', 'mobile', 'mobi'])
        qr_code_base64 = None
    
    context = {
        'payment': payment,
        'bill_split': bill_split,
        'payment_url': payment_url,
        'fallback_url': fallback_url,
        'upi_links': upi_links,
        'qr_code_base64': qr_code_base64,
        'debug_info': {
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'is_mobile': is_mobile,
            'platform': request.META.get('HTTP_SEC_CH_UA_PLATFORM', 'Unknown').replace('"', '')
        }
    }
    return render(request, 'bills/payment_redirect.html', context)
