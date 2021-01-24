from django.shortcuts import render
from .models import Vacancy

# Create your views here.
def home_view(request):
    qs = Vacancy.objects.all()
    return render(request, 'scraping/home.html', {'object_list': qs})