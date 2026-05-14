from django.urls import path
from . import views

urlpatterns = [
    path('candidate-dashboard-stats/', views.candidate_dashboard_stats, name='candidate_dashboard_stats'),
    path('get-profile-view/', views.get_profile_view, name='get-profile-view'),
    path('save-profile-view/', views.save_profile_view, name='save-profile-view'),
    path('submit-application/', views.submit_application, name='submit-application')
]