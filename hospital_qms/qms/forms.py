from django import forms
from .models import Department, Doctor, Patient, PatientCareAssignment

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'care_of', 'address', 'phone', 'department', 'doctor', 'emergency']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'department', 'role', 'room', 'days']

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

class PatientCareAssignmentForm(forms.ModelForm):
    class Meta:
        model = PatientCareAssignment
        fields = ['user', 'department']