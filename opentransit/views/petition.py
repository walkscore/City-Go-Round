import time
import logging
from google.appengine.ext import db
from ..forms import PetitionForm
from ..utils.view import render_to_response, redirect_to, not_implemented
from ..models import PetitionModel

def example_petition_form(request):
    # This example page handles the petition form!
    # This is how you typically handle forms in Django.
    # Again, it is only an example!        
    if request.method == 'POST':
        form = PetitionForm(request.POST)
        if form.is_valid():
            model = PetitionModel()
            model.name = form.cleaned_data['name']
            model.email = form.cleaned_data['email']
            model.city = form.cleaned_data['city']
            model.state = form.cleaned_data['state']
            model.country = form.cleaned_data['country']
            model.put()
            return redirect_to('example_petition_success')
    else:
        form = PetitionForm()
        
    return render_to_response(request, 'example_petition_form.html', {'form': form})

def example_petition_success(request):
    return render_to_response(request, 'example_petition_success.html')

