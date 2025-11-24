from django.contrib import admin
from .models import Department, Doctor, Patient, PatientCareAssignment, PatientLine

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'role', 'room', 'days']
    list_filter = ['department', 'role']
    search_fields = ['name']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['mrn', 'name', 'age', 'gender', 'department', 'emergency', 'created_at']
    list_filter = ['department', 'emergency', 'gender']
    search_fields = ['name', 'mrn', 'phone']

@admin.register(PatientCareAssignment)
class PatientCareAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'department']
    list_filter = ['department']

@admin.register(PatientLine)
class PatientLineAdmin(admin.ModelAdmin):
    list_display = ['patient', 'queue_type', 'status', 'room', 'order_index', 'created_at']
    list_filter = ['queue_type', 'status', 'patient__department']  # Fixed: Changed 'department' to 'patient__department'
    search_fields = ['patient__name', 'patient__mrn']