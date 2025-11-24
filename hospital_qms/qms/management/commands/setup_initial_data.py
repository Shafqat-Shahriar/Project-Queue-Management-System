# qms/management/commands/setup_initial_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from qms.models import Department, Doctor, PatientCareAssignment

class Command(BaseCommand):
    help = 'Sets up initial data for the Hospital QMS'

    def handle(self, *args, **options):
        # Create groups
        counter_group, _ = Group.objects.get_or_create(name='Counter')
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        patient_care_group, _ = Group.objects.get_or_create(name='Patient Care')
        
        # Create users
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user('admin', password='admin123')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))
        
        if not User.objects.filter(username='counter').exists():
            counter_user = User.objects.create_user('counter', password='counter123')
            counter_user.groups.add(counter_group)
            counter_user.save()
            self.stdout.write(self.style.SUCCESS('Created counter user: counter/counter123'))
        
        if not User.objects.filter(username='admin_user').exists():
            admin_user = User.objects.create_user('admin_user', password='admin123')
            admin_user.groups.add(admin_group)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin_user/admin123'))
        
        if not User.objects.filter(username='patient_care').exists():
            patient_care_user = User.objects.create_user('patient_care', password='care123')
            patient_care_user.groups.add(patient_care_group)
            patient_care_user.save()
            self.stdout.write(self.style.SUCCESS('Created patient care user: patient_care/care123'))
        
        # Create departments
        departments = [
            'Cataract', 'Retina', 'Glaucoma', 'Cornea', 'Private', 'General'
        ]
        
        for dept_name in departments:
            department, _ = Department.objects.get_or_create(name=dept_name)
        
        # Create some doctors
        general_dept = Department.objects.get(name='General')
        
        doctors = [
            {'name': 'Dr. John Smith', 'role': 'doctor', 'room': 'B1', 'days': 'Mon,Tue,Wed,Thu,Fri'},
            {'name': 'Dr. Sarah Johnson', 'role': 'doctor', 'room': 'B2', 'days': 'Mon,Tue,Wed,Thu,Fri'},
            {'name': 'Dr. Michael Brown', 'role': 'optometrist', 'room': 'A1', 'days': 'Mon,Tue,Wed,Thu,Fri'},
            {'name': 'Dr. Emily Davis', 'role': 'optometrist', 'room': 'A2', 'days': 'Mon,Tue,Wed,Thu,Fri'},
        ]
        
        for doctor_data in doctors:
            doctor, _ = Doctor.objects.get_or_create(
                name=doctor_data['name'],
                defaults={
                    'department': general_dept,
                    'role': doctor_data['role'],
                    'room': doctor_data['room'],
                    'days': doctor_data['days']
                }
            )
        
        # Assign patient care user to general department
        patient_care_user = User.objects.get(username='patient_care')
        assignment, _ = PatientCareAssignment.objects.get_or_create(
            user=patient_care_user,
            defaults={'department': general_dept}
        )
        
        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))