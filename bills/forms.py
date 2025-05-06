from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Group, Bill, BillSplit, Payment

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True, help_text="Enter your phone number")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number']
            )
            
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'upi_id']
        widgets = {
            'upi_id': forms.TextInput(attrs={'placeholder': 'yourname@upi'})
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class AddMemberForm(forms.Form):
    phone_number = forms.CharField(max_length=15, required=True, help_text="Enter friend's phone number to add to group")

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['title', 'amount', 'description', 'group']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BillSplitForm(forms.Form):
    SPLIT_CHOICES = (
        ('equal', 'Equal Split'),
        ('custom', 'Custom Split'),
    )
    split_type = forms.ChoiceField(choices=SPLIT_CHOICES, widget=forms.RadioSelect, initial='equal')
    
    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        
        if group:
            # Dynamically add form fields for each member in the group
            for i, member in enumerate(group.members.all()):
                self.fields[f'member_{member.id}'] = forms.BooleanField(
                    label=member.username,
                    required=False,
                    initial=True
                )
                self.fields[f'amount_{member.id}'] = forms.DecimalField(
                    required=False,
                    widget=forms.NumberInput(attrs={'placeholder': '0.00'}),
                )

class PaymentForm(forms.ModelForm):
    PAYMENT_METHODS = (
        ('AMAZON', 'Amazon Pay'),
        ('GPAY', 'Google Pay'),
        ('PAYTM', 'Paytm'),
        ('UPI', 'UPI Payment'),
        ('OTHER', 'Other')
    )
    payment_method = forms.ChoiceField(choices=PAYMENT_METHODS, initial='UPI')
    upi_id = forms.CharField(max_length=50, required=False, 
                            widget=forms.TextInput(attrs={'placeholder': 'yourname@upi'}),
                            help_text="Enter UPI ID for payment")
    save_upi = forms.BooleanField(required=False, initial=True, 
                                 label="Save UPI ID for future payments")
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'upi_id']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill UPI ID if available
        if user and hasattr(user, 'profile') and user.profile.upi_id:
            self.fields['upi_id'].initial = user.profile.upi_id 