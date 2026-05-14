from django.urls import path

from . import views


from . import text_extraction

urlpatterns = [
    path('upload-resume/', text_extraction.upload_resume, name='upload_resume'),
    path('recent-activities/', views.recent_activities, name='recent_activities'),
]