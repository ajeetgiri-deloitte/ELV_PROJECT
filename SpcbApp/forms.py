from django import forms

class AttestedCertificateForm(forms.Form):
    attested_certificate = forms.FileField(
        label='Upload Attested Certificate',
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png',
            'class': 'form-control'
        })
    )