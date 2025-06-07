from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from .models import Vacancy
from .forms import FindForm
from .scrapers.linkedin_scraper import LinkedInScraper


# Create your views here.
def home_view(request):
    form = FindForm()
    return render(request, 'scraping/home.html', {'form': form})


def list_view(request):
    #print(request.GET)
    form = FindForm()
    city = request.GET.get('city')
    language = request.GET.get('language')
    context = {'city': city, 'language': language, 'form': form}
    if city or language:
        _filter = {}
        if city:
            _filter['city__slug'] = city
        if language:
            _filter['language__slug'] = language

        qs = Vacancy.objects.filter(**_filter)
        paginator = Paginator(qs, 10)

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['object_list'] = page_obj
    return render(request, 'scraping/list.html', context)


class LinkedInAuthView(View):
    def get(self, request):
        """Redirect to LinkedIn authorization page"""
        auth_url = LinkedInScraper.get_auth_url()
        return redirect(auth_url)


class LinkedInCallbackView(View):
    def get(self, request):
        """Handle LinkedIn OAuth callback"""
        code = request.GET.get('code')
        if not code:
            messages.error(request, "No authorization code received from LinkedIn")
            return redirect('home')  # Replace with your home URL name
            
        try:
            auth = LinkedInScraper.handle_auth_callback(code)
            messages.success(request, "Successfully authenticated with LinkedIn")
        except Exception as e:
            messages.error(request, f"Error authenticating with LinkedIn: {str(e)}")
            
        return redirect('home')  # Replace with your home URL name