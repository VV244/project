from django import forms
from django.core import signing
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    adult_confirmation = forms.BooleanField(label='I am a parent, guardian, or educator. I have read the privacy policy.')
    website = forms.CharField(required=False, label='Leave this empty', widget=forms.TextInput(attrs={'autocomplete': 'off', 'tabindex': '-1'}))
    form_token = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        labels = {'name': 'Your name', 'email': 'Email address', 'subject': 'What can we help with?', 'message': 'Your message'}
        widgets = {'message': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Please do not include children’s names, photos, or other personal details.'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['form_token'] = signing.dumps('contact', salt='contact-form')
        for name in ('name', 'email', 'subject', 'message'):
            self.fields[name].widget.attrs['class'] = 'form-control'

    def clean_message(self):
        value = self.cleaned_data['message'].strip()
        if len(value) < 20:
            raise forms.ValidationError('Please write at least 20 characters.')
        return value

    def clean(self):
        data = super().clean()
        if data.get('website'):
            raise forms.ValidationError('Unable to accept this form.')
        try:
            if signing.loads(data.get('form_token', ''), salt='contact-form', max_age=7200) != 'contact':
                raise signing.BadSignature
        except signing.BadSignature:
            raise forms.ValidationError('This form has expired. Refresh the page and try again.')
        return data
