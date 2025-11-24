from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('counter/', views.counter_dashboard, name='counter_dashboard'),
    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('patient-care/', views.patient_care_dashboard, name='patient_care_dashboard'),
    
    # Patient management
    path('register-patient/', views.register_patient, name='register_patient'),
    path('api/patient/<str:mrn>/', views.get_patient_by_mrn, name='get_patient_by_mrn'),
    
    # Admin management
    path('manage/departments/', views.manage_departments, name='manage_departments'),
    path('edit/department/<int:pk>/', views.edit_department, name='edit_department'),
    path('delete/department/<int:pk>/', views.delete_department, name='delete_department'),
    
    path('manage/doctors/', views.manage_doctors, name='manage_doctors'),
    path('edit/doctor/<int:pk>/', views.edit_doctor, name='edit_doctor'),
    path('delete/doctor/<int:pk>/', views.delete_doctor, name='delete_doctor'),
    
    path('manage/patient-care/', views.manage_patient_care_assignments, name='manage_patient_care_assignments'),
    path('delete/patient-care/<int:pk>/', views.delete_patient_care_assignment, name='delete_patient_care_assignment'),
    
    # Patient Care actions
    path('api/call-next/', views.call_next_patient, name='call_next_patient'),
    path('api/start-processing/', views.start_processing, name='start_processing'),
    path('api/complete-patient/', views.complete_patient, name='complete_patient'),
    path('api/hold-patient/', views.hold_patient, name='hold_patient'),
    path('api/return-to-queue/', views.return_to_queue, name='return_to_queue'),
]