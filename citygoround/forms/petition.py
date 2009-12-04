from django import forms

class PetitionForm(forms.Form):  
    name = forms.CharField(max_length = 128, min_length = 6, label = u"Name")
    email = forms.EmailField(label = u"Email")
    city = forms.CharField(max_length = 64, min_length = 3, label = u"City")
    state = forms.CharField(max_length = 16, min_length = 2, label = u"State")
    country = forms.CharField(max_length = 16, min_length = 2, label = u"Country")
