from django import forms
from captcha.fields import CaptchaField, CaptchaTextInput
from .models import *
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import *

from .models import CpcbUser


class LoginForm(forms.Form):
    # email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))
    username = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'id': 'username', 'class': 'form-control', 'placeholder': 'Enter Username', 'autocomplete': 'off', 'autocorrect': 'off', 'autocapitalize': 'none', 'spellcheck': 'false', 'onpaste': 'return false;', 'oncopy': 'return false;', 'oncut': 'return false;'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password', 'class': 'form-control', 'placeholder': 'Enter Password', 'autocomplete': 'new-password', 'autocorrect': 'off', 'autocapitalize': 'none', 'spellcheck': 'false', 'onpaste': 'return false;', 'oncopy': 'return false;', 'oncut': 'return false;'}))
    captcha = CaptchaField(
        widget=CaptchaTextInput(
            attrs={
                'class': 'form-control custom-captcha-input fst-italic',  # Add custom classes
                'placeholder': 'Enter Captcha',  # Add a placeholder
                'maxlength' : "6",
                'style': 'margin-top: 9px; ',  # Inline CSS styles
                
            }
        )
    )
    
class ProducerOTPForm(forms.Form):
    otp = forms.CharField(
        required=False,
        max_length=6,
        widget=forms.TextInput(attrs={
            'id': 'otp',
            'class': 'form-control',
            'placeholder': 'Enter OTP',
        })
    )
    captcha = CaptchaField(
        widget=CaptchaTextInput(attrs={
            'class': 'form-control custom-captcha-input fst-italic',
            'placeholder': 'Enter Captcha',
            'maxlength': '6',
            'style': 'margin-top: 9px;',
        })
    )
    
class CaptchaForm(forms.Form):
    captcha = CaptchaField(
        widget=CaptchaTextInput(
            attrs={
                'class': 'form-control custom-captcha-input fst-italic',  # Add custom classes
                'placeholder': 'Enter Captcha',  # Add a placeholder
                'maxlength' : "6",
                'style': 'margin-top: 9px; ',  # Inline CSS styles
                
            }
        )
    )
    
class CpcbLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class CpcbOTPForm(forms.Form):
    otp = forms.CharField(max_length=6)
    

class CpcbUserForm(forms.ModelForm):
    captcha = CaptchaField(
        widget=CaptchaTextInput(
            attrs={
                'class': 'form-control custom-captcha-input fst-italic',
                'placeholder': 'Enter Captcha',
                'maxlength': "6",
                'style': 'margin-top: 9px;',
            }
        )
    )

    class Meta:
        model = CpcbUser
        fields = ['first_name', 'last_name', 'email', 'division', 'mobile_no']

    # Custom validators
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CpcbUser.objects.filter(email=email).exists():
            raise ValidationError("Email already registered.")
        return email

    def clean_mobile_no(self):
        mobile_no = self.cleaned_data.get('mobile_no')
        if not mobile_no.isdigit() or len(mobile_no) != 10:
            raise ValidationError("Enter a valid 10-digit mobile number.")
        return mobile_no
    
class ChecklistForm(forms.Form):
    producer_name_address = forms.ChoiceField(
        label='Producer Name and Address',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    
    remarks_producer_name_address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',  # To avoid a separate label column
    )

    company_email = forms.ChoiceField(
        label='Company Email',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_company_email = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    upload_gst_certificate = forms.ChoiceField(
        label='Uploaded GST certificate',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_upload_gst_certificate = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    year_of_incorporation = forms.ChoiceField(
        label='Year of Incorporation',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_year_of_incorporation = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    pan_card_uploaded = forms.ChoiceField(
        label='Provided and Uploaded PAN card of company',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_pan_card_uploaded = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    tin_certificate_uploaded = forms.ChoiceField(
        label='Provided and Uploaded TIN Certificate',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_tin_certificate_uploaded = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    cin_certificate_uploaded = forms.ChoiceField(
        label='Provided and Uploaded CIN Certificate',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_cin_certificate_uploaded = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    iec_certificate_uploaded = forms.ChoiceField(
        label='Provided and Uploaded IEC Certificate',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_iec_certificate_uploaded = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    authorized_person_details = forms.ChoiceField(
        label='Authorized Person Details (Name, Email ID, Mobile No)',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_authorized_person_details = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    authorized_person_pan_details = forms.ChoiceField(
        label='Provided and Uploaded Authorized Person PAN Card',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_authorized_person_pan_details = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    nature_of_business = forms.ChoiceField(
        label='Nature of Business',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_nature_of_business = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    
    name_address_facility = forms.ChoiceField(
        label='Name, Address and GST of the Facility',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_name_address_facility = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    activity_type = forms.ChoiceField(
        label='Provided Activity type',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_activity_type = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    capacity_of_facility = forms.ChoiceField(
        label='Provided Capacity of facility',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_capacity_of_facility = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    # data_transport_vehicles = forms.ChoiceField(
    #     label='Provided Data on Transport vehicles',
    #     choices=[('yes', 'Yes'), ('no', 'No')],
    #     widget=forms.RadioSelect,
    #     required=False,
    # )
    # remarks_data_transport_vehicles = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2}),
    #     required=False,
    #     label='',
    # )

    data_transport = forms.ChoiceField(
        label='Provided Data on Transport vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    fy_data_transport = forms.ChoiceField(
        label='Provided all Financial year Data',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_fy_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    vehicle_data_transport = forms.ChoiceField(
        label='Provided all types of Vehicle Data',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_vehicle_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    manufactured_data_transport = forms.ChoiceField(
        label='Provided Data on manufactured/imported/Procurement of vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_manufactured_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    open_market_sales_data_transport = forms.ChoiceField(
        label='Provided Open Market Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_open_market_sales_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    other_producer_sales_data_transport = forms.ChoiceField(
        label='Provided Other Producer Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_other_producer_sales_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    cobranding_sales_data_transport = forms.ChoiceField(
        label='Provided Cobranding Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_cobranding_sales_data_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    uploaded_excel_other_producer_standard_format_transport = forms.ChoiceField(
        label='Uploaded Excel for sold to other producer/cobranded as per standard format',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_excel_other_producer_standard_format_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    self_use_transport = forms.ChoiceField(
        label='Provided Details of Self use Vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_self_use_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    exported_vehicles_transport = forms.ChoiceField(
        label='Provided Details of Exported Vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_exported_vehicles_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    uploaded_ca_certificates_each_fy_transport = forms.ChoiceField(
        label='Uploaded CA Certificates for each FY',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_ca_certificates_each_fy_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    # data_non_transport_vehicles = forms.ChoiceField(
    #     label='Provided Data on Non Transport vehicles',
    #     choices=[('yes', 'Yes'), ('no', 'No')],
    #     widget=forms.RadioSelect,
    #     required=False,
    # )
    # remarks_data_non_transport_vehicles = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 2}),
    #     required=False,
    #     label='',
    # )

    data_non_transport = forms.ChoiceField(
        label='Provided Data on Transport vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    fy_data_non_transport = forms.ChoiceField(
        label='Provided all Financial year Data',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_fy_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    vehicle_data_non_transport = forms.ChoiceField(
        label='Provided all types of Vehicle Data',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_vehicle_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    manufactured_data_non_transport = forms.ChoiceField(
        label='Provided Data on manufactured/imported/Procurement of vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_manufactured_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    open_market_sales_data_non_transport = forms.ChoiceField(
        label='Provided Open Market Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_open_market_sales_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    other_producer_sales_data_non_transport = forms.ChoiceField(
        label='Provided Other Producer Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_other_producer_sales_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    cobranding_sales_data_non_transport = forms.ChoiceField(
        label='Provided Cobranding Sales Details',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_cobranding_sales_data_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    uploaded_excel_standard_format_non_transport = forms.ChoiceField(
        label='Uploaded Excel for sold to other producer/cobranded as per standard format',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_excel_standard_format_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    self_use_non_transport = forms.ChoiceField(
        label='Provided Details of Self use Vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_self_use_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    exported_vehicles_non_transport = forms.ChoiceField(
        label='Provided Details of Exported Vehicles',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_exported_vehicles_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    uploaded_ca_certificates_each_fy_non_transport = forms.ChoiceField(
        label='Uploaded CA Certificates for each FY',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_ca_certificates_each_fy_non_transport = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    provided_annual_turnover_both_fy = forms.ChoiceField(
        label='Provided the Annual turnover for Both FY (2023-2024, 2024-2025)',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_provided_annual_turnover_both_fy = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )

    uploaded_ca_certificate_each_fy = forms.ChoiceField(
        label='Uploaded CA Certificates for Annual turnover for Both FY (2023-2024, 2024-2025)',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_ca_certificate_each_fy = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    uploaded_undertaking = forms.ChoiceField(
        label='Uploaded Undertaking',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_uploaded_undertaking = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    
    reg_fee = forms.ChoiceField(
        label='Registration Fee payment done',
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.RadioSelect,
        required=False,
    )
    remarks_reg_fee = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='',
    )
    

class SaveChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = '__all__'


class NotingForm(forms.ModelForm):
    class Meta:
        model = Noting
        fields = ['comment']