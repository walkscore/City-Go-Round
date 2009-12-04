from django import forms

class ContactForm(forms.Form):  
    name = forms.CharField(max_length = 128, min_length = 6, label = u"Name")
    email = forms.EmailField(label = u"Email")
    message = forms.CharField(min_length = 0, max_length = 2048, widget = forms.widgets.Textarea(attrs = {'rows': 6, 'cols': 32}), label = u"Message")
    