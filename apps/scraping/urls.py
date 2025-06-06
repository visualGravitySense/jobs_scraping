from django.urls import path
from .views import (
    home_view, list_view, v_detail, v_create, v_update, v_delete,
    LinkedInAuthView, LinkedInCallbackView
)

urlpatterns = [
    path('', home_view, name='home'),
    path('list/', list_view, name='list'),
    path('detail/<int:pk>/', v_detail, name='v_detail'),
    path('create/', v_create, name='v_create'),
    path('update/<int:pk>/', v_update, name='v_update'),
    path('delete/<int:pk>/', v_delete, name='v_delete'),
    
    # LinkedIn authentication URLs
    path('linkedin/auth/', LinkedInAuthView.as_view(), name='linkedin_auth'),
    path('linkedin/callback/', LinkedInCallbackView.as_view(), name='linkedin_callback'),
] 