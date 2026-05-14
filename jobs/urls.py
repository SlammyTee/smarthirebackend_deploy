from django.urls import path
from . import views

urlpatterns = [
    path('create-job/', views.create_job, name='create_job'),
    path('jobs-with-applicants/', views.get_jobs_with_applicants, name='jobs_with_applicants'),
    path('jobs/', views.get_jobs, name='jobs'),
    path('get-applications', views.get_my_applications, name='get-applications'),
    path('hr-dashboard-stats/', views.hr_dashboard_stats, name='hr_dashboard_stats'),
    path('admin-dashboard-stats/', views.admin_dashboard_stats, name='admin_dashboard_stats'),
    path('get-applicants/', views.get_applicants, name ='get_applicants' ),
    path('applications/<uuid:pk>/status/', views.update_application_status),
    path('job/<uuid:job_id>/delete/', views.delete_job, name='delete_job'),
    path('recommended-jobs/' ,views.recommended_jobs, name='recommended_jobs' ),
    path( "send-interview-invite/<uuid:pk>/",views.send_interview_invite, name="send_interview_invite"),
]