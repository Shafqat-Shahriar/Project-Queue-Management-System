from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Doctor(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('optometrist', 'Optometrist'),
    ]
    
    ROOM_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'),
        ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'), ('B5', 'B5'),
    ]
    
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    room = models.CharField(max_length=5, choices=ROOM_CHOICES)
    days = models.CharField(max_length=20, help_text="e.g., Mon,Tue,Wed")
    
    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    care_of = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    mrn = models.CharField(max_length=20, unique=True, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    emergency = models.BooleanField(default=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.mrn})"
    
    def save(self, *args, **kwargs):
        if not self.mrn:
            current_year = datetime.datetime.now().year
            last_patient = Patient.objects.filter(mrn__startswith=f"MRN-{current_year}-").order_by('-mrn').first()
            
            if last_patient:
                last_number = int(last_patient.mrn.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.mrn = f"MRN-{current_year}-{new_number:04d}"
        
        super().save(*args, **kwargs)

class PatientCareAssignment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username} - {self.department.name}"

class PatientLine(models.Model):
    QUEUE_TYPE_CHOICES = [
        ('optometrist', 'Optometrist'),
        ('doctor', 'Doctor'),
    ]
    
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('calling', 'Calling'),
        ('processing', 'Processing'),
        ('hold', 'Hold'),
        ('completed', 'Completed'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    queue_type = models.CharField(max_length=20, choices=QUEUE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    room = models.CharField(max_length=5, blank=True)
    order_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order_index', 'created_at']
    
    def __str__(self):
        return f"{self.patient.name} - {self.get_queue_type_display()} - {self.get_status_display()}"