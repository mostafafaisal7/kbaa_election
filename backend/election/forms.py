from django import forms
from .models import Nomination, FormLabel,Vote, Position

class NominationForm(forms.ModelForm):
    class Meta:
        model = Nomination
        fields = [
            'full_name',
            'email',
            'gender',
            'designation',
            'workplace_address',
            'interested',
            'desired_position',
            'photo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set labels from admin-editable FormLabel
        for field_name, field in self.fields.items():
            try:
                label_obj = FormLabel.objects.get(form_type='nominee', field_name=field_name)
                field.label = label_obj.label_text
            except FormLabel.DoesNotExist:
                # fallback to default field label
                pass

        # Extra security & usability
        self.fields['email'].widget.attrs.update({'placeholder': 'Enter a valid email'})
        self.fields['full_name'].widget.attrs.update({'placeholder': 'Enter your full name'})
        self.fields['photo'].widget.attrs.update({'accept': 'image/jpeg,image/png'})



class VoteForm(forms.Form):
    # Voter info
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    gender = forms.ChoiceField(choices=[('Male','Male'),('Female','Female')])
    designation = forms.CharField(max_length=100)
    workplace_address = forms.CharField(max_length=255)
    last_training_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))

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
