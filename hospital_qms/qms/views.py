from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from .models import Department, Doctor, Patient, PatientCareAssignment, PatientLine
from .forms import PatientForm, DoctorForm, DepartmentForm, PatientCareAssignmentForm


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if user.is_superuser:
                return redirect('admin_dashboard')

            if user.groups.filter(name='Counter').exists():
                return redirect('counter_dashboard')

            if user.groups.filter(name='Admin').exists():
                return redirect('admin_dashboard')

            if user.groups.filter(name='Patient Care').exists():
                return redirect('patient_care_dashboard')

            return redirect('login')

        return render(request, 'qms/login.html', {'error': 'Invalid credentials'})

    return render(request, 'qms/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------------------------------------------------
# DASHBOARD VIEWS
# ---------------------------------------------------------

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    departments = Department.objects.all()
    doctors = Doctor.objects.all()

    return render(request, 'qms/admin_dashboard.html', {
        'departments': departments,
        'doctors': doctors,
    })


@login_required
def counter_dashboard(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Counter').exists():
        return redirect('login')

    recent_patients = Patient.objects.all().order_by('-created_at')[:10]
    departments = Department.objects.all()

    return render(request, 'qms/counter_dashboard.html', {
        'recent_patients': recent_patients,
        'departments': departments,
    })

@login_required
def patient_care_dashboard(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')
    
    try:
        assignment = PatientCareAssignment.objects.get(user=request.user)
        department = assignment.department
        
        # Get the queues for this department
        # --- THIS IS THE CORRECTED CODE ---
        optometrist_queue = PatientLine.objects.filter(
            patient__department=department,
            queue_type='optometrist',
            status__in=['waiting', 'calling', 'processing']
        ).order_by('order_index', 'created_at')
        
        doctor_queue = PatientLine.objects.filter(
            patient__department=department,
            queue_type='doctor',
            status__in=['waiting', 'calling', 'processing']
        ).order_by('order_index', 'created_at')
        
        # Get available rooms
        optometrist_rooms = Doctor.objects.filter(
            department=department,
            role='optometrist'
        ).values_list('room', flat=True)
        
        doctor_rooms = Doctor.objects.filter(
            department=department,
            role='doctor'
        ).values_list('room', flat=True)

        # Check if there is at least one available room for each queue type
        optometrist_available_room = get_available_room(department.id, 'optometrist')
        doctor_available_room = get_available_room(department.id, 'doctor')
        
        context = {
            'department': department,
            'optometrist_queue': optometrist_queue,
            'doctor_queue': doctor_queue,
            'optometrist_rooms': optometrist_rooms,
            'doctor_rooms': doctor_rooms,
            'optometrist_available': optometrist_available_room is not None,
            'doctor_available': doctor_available_room is not None,
        }
        
        return render(request, 'qms/patient_care_dashboard.html', context)
    except PatientCareAssignment.DoesNotExist:
        return render(request, 'qms/no_assignment.html')

# ... other views
# ---------------------------------------------------------
# PATIENT REGISTRATION
# ---------------------------------------------------------

@login_required
def register_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()

            # If specific doctor selected
            if patient.doctor:
                PatientLine.objects.create(
                    patient=patient,
                    queue_type=patient.doctor.role,
                    status='waiting',
                    order_index=get_next_order_index(
                        patient.department,
                        patient.doctor.role,
                        patient
                    )
                )
            else:
                # Default: optometrist queue
                PatientLine.objects.create(
                    patient=patient,
                    queue_type='optometrist',
                    status='waiting',
                    order_index=get_next_order_index(
                        patient.department,
                        'optometrist',
                        patient
                    )
                )

            return JsonResponse({'success': True, 'mrn': patient.mrn})

        return JsonResponse({'success': False, 'errors': form.errors})

    departments = Department.objects.all()
    return render(request, 'qms/register_patient.html', {'departments': departments})


@login_required
def get_patient_by_mrn(request, mrn):
    if not Group.objects.get(name='Counter') in request.user.groups.all() and not request.user.is_superuser:
        return redirect('login')

    try:
        patient = Patient.objects.get(mrn=mrn)

        return JsonResponse({
            'success': True,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'care_of': patient.care_of,
            'address': patient.address,
            'phone': patient.phone,
            'department_id': patient.department.id,
            'doctor_id': patient.doctor.id if patient.doctor else None,
        })

    except Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


# ---------------------------------------------------------
# ADMIN MANAGEMENT VIEWS
# ---------------------------------------------------------

@login_required
def manage_departments(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')

    return render(request, 'qms/manage_departments.html', {
        'departments': Department.objects.all(),
        'form': DepartmentForm(),
    })


@login_required
def edit_department(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('manage_departments')

    return render(request, 'qms/edit_department.html', {
        'form': DepartmentForm(instance=department),
        'department': department,
    })


@login_required
def delete_department(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    get_object_or_404(Department, pk=pk).delete()
    return redirect('manage_departments')


@login_required
def manage_doctors(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_doctors')

    return render(request, 'qms/manage_doctors.html', {
        'doctors': Doctor.objects.all(),
        'form': DoctorForm(),
    })


@login_required
def edit_doctor(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('manage_doctors')

    return render(request, 'qms/edit_doctor.html', {
        'form': DoctorForm(instance=doctor),
        'doctor': doctor,
    })


@login_required
def delete_doctor(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    get_object_or_404(Doctor, pk=pk).delete()
    return redirect('manage_doctors')


@login_required
def manage_patient_care_assignments(request):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    if request.method == 'POST':
        form = PatientCareAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_patient_care_assignments')

    return render(request, 'qms/manage_patient_care_assignments.html', {
        'assignments': PatientCareAssignment.objects.all(),
        'form': PatientCareAssignmentForm(),
    })


@login_required
def delete_patient_care_assignment(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    get_object_or_404(PatientCareAssignment, pk=pk).delete()
    return redirect('manage_patient_care_assignments')


# ---------------------------------------------------------
# PATIENT CARE ACTIONS
# ---------------------------------------------------------

@login_required
@require_http_methods(["POST"])
def call_next_patient(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')

    queue_type = request.POST.get('queue_type')
    department_id = request.POST.get('department_id')

    next_patient_line = PatientLine.objects.filter(
        patient__department_id=department_id,
        queue_type=queue_type,
        status='waiting'
    ).order_by('order_index', 'created_at').first()

    if next_patient_line:
        available_room = get_available_room(department_id, queue_type)

        if available_room:
            next_patient_line.status = 'calling'
            next_patient_line.room = available_room
            next_patient_line.save()

            return JsonResponse({
                'success': True,
                'patient_id': next_patient_line.patient.id,
                'patient_name': next_patient_line.patient.name,
                'room': available_room,
            })

    return JsonResponse({'success': False, 'error': 'No patients or rooms available'})


@login_required
@require_http_methods(["POST"])
def start_processing(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')

    patient_line_id = request.POST.get('patient_line_id')

    try:
        patient_line = PatientLine.objects.get(id=patient_line_id)
        patient_line.status = 'processing'
        patient_line.save()

        return JsonResponse({'success': True})

    except PatientLine.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


@login_required
@require_http_methods(["POST"])
def complete_patient(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')

    patient_line_id = request.POST.get('patient_line_id')

    try:
        patient_line = PatientLine.objects.select_related('patient').get(id=patient_line_id)

        # If patient finished optometrist → send to doctor queue
        if patient_line.queue_type == 'optometrist':

            already_in_doctor_queue = PatientLine.objects.filter(
                patient=patient_line.patient,
                queue_type='doctor',
                status__in=['waiting', 'calling', 'processing']
            ).exists()

            if not already_in_doctor_queue:
                PatientLine.objects.create(
                    patient=patient_line.patient,
                    queue_type='doctor',
                    status='waiting',
                    order_index=get_next_order_index(
                        patient_line.patient.department,
                        'doctor',
                        patient_line.patient
                    )
                )

        patient_line.status = 'completed'
        patient_line.save()

        return JsonResponse({'success': True})

    except PatientLine.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


@login_required
@require_http_methods(["POST"])
def hold_patient(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')

    patient_line_id = request.POST.get('patient_line_id')

    try:
        patient_line = PatientLine.objects.get(id=patient_line_id)
        patient_line.status = 'hold'
        patient_line.room = ''
        patient_line.save()

        return JsonResponse({'success': True})

    except PatientLine.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


@login_required
@require_http_methods(["POST"])
def return_to_queue(request):
    if not request.user.groups.filter(name='Patient Care').exists():
        return redirect('login')

    patient_line_id = request.POST.get('patient_line_id')

    try:
        patient_line = PatientLine.objects.get(id=patient_line_id)
        patient_line.status = 'waiting'
        patient_line.room = ''
        patient_line.save()

        return JsonResponse({'success': True})

    except PatientLine.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})


# ---------------------------------------------------------
# QUEUE ORDER HELPER
# ---------------------------------------------------------

def get_next_order_index(department, queue_type, patient=None):
    waiting_lines = PatientLine.objects.filter(
        patient__department=department,
        queue_type=queue_type,
        status='waiting'
    ).order_by('order_index')

    if not waiting_lines.exists():
        return 1

    # Emergency placed at front
    if patient and getattr(patient, "emergency", False):
        first_index = waiting_lines.first().order_index
        return first_index / 2.0

    # Normal → end of queue
    last_index = waiting_lines.last().order_index
    return last_index + 1


# ---------------------------------------------------------
# ROOM AVAILABILITY
# ---------------------------------------------------------

def get_available_room(department_id, queue_type):
    all_rooms = Doctor.objects.filter(
        department_id=department_id,
        role=queue_type
    ).values_list('room', flat=True)

    occupied_rooms = PatientLine.objects.filter(
        patient__department_id=department_id,
        queue_type=queue_type,
        status__in=['calling', 'processing']
    ).values_list('room', flat=True)

    for room in all_rooms:
        if room not in occupied_rooms:
            return room

    return None


# ---------------------------------------------------------
# API ENDPOINT – Doctors by Department
# ---------------------------------------------------------

@login_required
def get_doctors_by_department(request, department_id):
    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        return redirect('login')

    doctors = Doctor.objects.filter(department_id=department_id)

    return JsonResponse({
        'success': True,
        'doctors': [{'id': d.id, 'name': d.name, 'role': d.role} for d in doctors]
    })
