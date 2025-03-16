from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password

from apps.scraping.models import City, Language


User = get_user_model()


class FindForm(forms.Form):
    city = forms.ModelChoiceField(queryset=City.objects.all(), to_field_name="slug", required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
                                  label='City'
    )
    language = forms.ModelChoiceField(queryset=Language.objects.all(), to_field_name="slug", required=False,
                                      widget=forms.Select(attrs={'class': 'form-control'}),
                                      label='Specialty'
    )
    #name = forms.CharField(initial='class')

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Enter email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Enter password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        data = self.cleaned_data
        if data['password'] != data['password2']:
            raise forms.ValidationError('Passwords do not match!')
        return data['password2']


class UserUpdateForm(forms.Form):
    city = forms.ModelChoiceField(
        queryset=City.objects.all(), to_field_name="slug", required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='City'
    )
    language = forms.ModelChoiceField(
        queryset=Language.objects.all(), to_field_name="slug", required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Specialty'
    )
    send_email = forms.BooleanField(required=False, widget=forms.CheckboxInput,
                                    label='Receive newsletter?')

    class Meta:
        model = User
        fields = ('city', 'language', 'send_email')


class ContactForm(forms.Form):
    city = forms.CharField(
        required=True,  widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='City'
    )
    language = forms.CharField(
        required=True,  widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Specialty'
    )
    email = forms.EmailField(
        label='Enter email', required=True, widget=forms.EmailInput(
                                 attrs={'class': 'form-control'})
    )
