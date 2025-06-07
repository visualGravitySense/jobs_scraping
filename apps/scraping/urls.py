from django.urls import path
from .views import (
    home_view, list_view, 
    LinkedInAuthView, LinkedInCallbackView, parsed_jobs_list_view
)

urlpatterns = [
    path('', home_view, name='home'),
    path('list/', list_view, name='list'),
    # LinkedIn authentication URLs
    path('linkedin/auth/', LinkedInAuthView.as_view(), name='linkedin_auth'),
    path('linkedin/callback/', LinkedInCallbackView.as_view(), name='linkedin_callback'),
    path('jobs/', list_view, name='jobs_list'),
    path('parsed-jobs/', parsed_jobs_list_view, name='parsed_jobs_list'),
] 