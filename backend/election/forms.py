from django import forms
from .models import Nomination, FormLabel, Vote, Position


class NominationForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )
    
    interested = forms.ChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )

    class Meta:
        model = Nomination
        fields = [
            'full_name',
            'email',
            'phone_number',  # NEW
            'gender',
            'designation',
            'workplace_address',
            'last_training_date',  # NEW
            'photo',
            'interested',
            'desired_position',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name Here...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Write Your Email...'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+008...'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write Here...'}),
            'workplace_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write Here...'}),
            'last_training_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'Select Date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/jpg,image/png'}),
            'desired_position': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set labels from admin-editable FormLabel
        for field_name, field in self.fields.items():
            try:
                label_obj = FormLabel.objects.get(form_type='nominee', field_name=field_name)
                field.label = label_obj.label_text
            except FormLabel.DoesNotExist:
                # Fallback to default field labels
                pass

        # Set default labels if FormLabel doesn't exist
        default_labels = {
            'full_name': 'Full Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'gender': 'Select Gender',
            'designation': 'Present Designation / Retired Designation',
            'workplace_address': 'Present Organization & Department / Last Organization & Department',
            'last_training_date': 'Last KOICA Training Date',
            'photo': 'Candidate Photo (Please Upload Passport Size)',
            'interested': 'Are You Interested In Becoming A Candidate For The KBAA Executive Committee Election 2025?',
            'desired_position': 'Desired Position In The KBAA Executive Committee',
        }

        for field_name, label in default_labels.items():
            if field_name in self.fields and not self.fields[field_name].label:
                self.fields[field_name].label = label

        # Make last_training_date optional (not required)
        self.fields['last_training_date'].required = False
        self.fields['phone_number'].required = True




class VoteForm(forms.Form):
    # Voter info
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
    designation = forms.CharField(max_length=100)
    workplace_address = forms.CharField(max_length=255)
    last_training_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    # Voting for one position at a time
    position_id = forms.IntegerField(widget=forms.HiddenInput)
    candidate = forms.ChoiceField(widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session')  # current session
        position = kwargs.pop('position')  # current position
        super().__init__(*args, **kwargs)

        self.fields['position_id'].initial = position.id

        # Get approved candidates for this position and session
        candidates = Nomination.objects.filter(
            session=session,
            desired_position=position,
            approved=True
        )
        choices = [(c.id, f"{c.full_name} ({c.designation})") for c in candidates]
        self.fields['candidate'].choices = choices