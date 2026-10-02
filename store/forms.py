from django import forms
from .models import ContactInquiry, Address, Order, NewsletterSubscriber


class ContactForm(forms.ModelForm):
    """Luxury Atelier Concierge inquiry form."""
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Radhika Singhania',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'name@example.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 98765 43210',
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }, choices=[
                ('Bespoke Bridal Consultation', 'Bespoke Bridal Consultation'),
                ('Order Tracking & Delivery', 'Order Tracking & Delivery'),
                ('Product Sizing & Customization', 'Product Sizing & Customization'),
                ('Private Exhibition Invitation', 'Private Exhibition Invitation'),
                ('General Inquiry', 'General Inquiry'),
            ]),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your inquiry, ceremony date, or creation of interest...',
                'required': True,
            }),
        }


class CheckoutForm(forms.Form):
    """Customer information and shipping address validation for checkout."""
    full_name = forms.CharField(max_length=200, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    postal_code = forms.CharField(max_length=30, required=True)
    payment_method = forms.ChoiceField(choices=[
        ('Cash on Delivery', 'Cash on Delivery'),
        ('Online Prepaid (UPI / Cards / NetBanking)', 'Online Prepaid (UPI / Cards / NetBanking)'),
    ], required=True)
    notes = forms.CharField(max_length=500, required=False)
    save_address = forms.BooleanField(required=False)
    saved_address_id = forms.IntegerField(required=False)


class AddressForm(forms.ModelForm):
    """Saved customer delivery address form."""
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210', 'required': True}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House / Flat / Suite No.', 'required': True}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, Area, Landmark'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'required': True}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'required': True}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN Code', 'required': True}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country', 'value': 'India'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NewsletterForm(forms.ModelForm):
    """Private Client Privileges subscription form."""
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address...',
                'required': True,
            })
        }


class TrackPackageForm(forms.Form):
    """Consignment order tracking form."""
    order_number = forms.CharField(max_length=50, required=True)
    identifier = forms.CharField(max_length=100, required=False)
