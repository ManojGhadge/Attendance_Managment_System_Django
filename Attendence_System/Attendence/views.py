# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from .models import Teacher, Student, Course, Attendance, Admin, StudentCourse
from django.db.models import Q, Count
from datetime import datetime, date
import csv
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied



# def home(request):
#     # Option: Redirect to teacher_login page
#     return redirect('teacher_login')
#     # Or render a home page template
#     # return render(request, 'home.html')

def home(request):
    return render(request, 'home.html')

# Teacher Login View
@require_http_methods(["GET", "POST"])
def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            teacher = Teacher.objects.get(username=username)
            if check_password(password, teacher.password):
                request.session['teacher_username'] = teacher.username
                request.session['teacher_name'] = teacher.teacher_name
                messages.success(request, f"Welcome back, {teacher.teacher_name}!")
                return redirect('teacher_dashboard')
            else:
                messages.error(request, "Invalid credentials")
        except Teacher.DoesNotExist:
            messages.error(request, "Invalid credentials")
    
    return render(request, 'teacher_login.html')



# Teacher Dashboard
def teacher_dashboard(request):
    if 'teacher_username' not in request.session:
        return redirect('teacher_login')
    
    username = request.session['teacher_username']
    teacher = Teacher.objects.get(username=username)
    
    # Get recent attendance records
    recent_attendances = Attendance.objects.filter(
        course_name__teacher=teacher
    ).order_by('-attendance_date')[:5]
    
    context = {
        'teacher_name': teacher.teacher_name,
        'recent_attendances': recent_attendances
    }
    return render(request, 'teacher_dashboard.html', context)



# Mark Attendance View
@require_http_methods(["GET", "POST"])
def mark_attendance(request):
    if 'teacher_username' not in request.session:
        return redirect('teacher_login')
    
    username = request.session['teacher_username']
    teacher = Teacher.objects.get(username=username)
    courses = Course.objects.filter(teacher=teacher)
    students = []
    today = date.today()
    
    # Get selected course from GET request
    selected_course = request.GET.get('course_name')
    if selected_course:
        try:
            course = Course.objects.get(course_name=selected_course, teacher=teacher)
            students = Student.objects.filter(studentcourse__course_name=course)
        except Course.DoesNotExist:
            messages.error(request, "Invalid course selected")
    
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        attendance_date = request.POST.get('attendance_date')
        
        if not course_name or not attendance_date:
            messages.error(request, "Please fill in all required fields")
            return redirect('mark_attendance')
        
        try:
            course = Course.objects.get(course_name=course_name, teacher=teacher)
            students = Student.objects.filter(studentcourse__course_name=course)
            
            # Convert attendance_date string to date object
            attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            
            # Check if attendance date is before course creation date
            if attendance_date_obj < course.created_at.date():
                messages.error(request, f"Attendance date cannot be before course creation date ({course.created_at.date()})")
                return redirect('mark_attendance')
            
            # Check if attendance date is in the future
            if attendance_date_obj > today:
                messages.error(request, "Cannot mark attendance for future dates")
                return redirect('mark_attendance')
            
            # Check if attendance for this date and course already exists
            existing_attendance = Attendance.objects.filter(
                course_name=course,
                attendance_date=attendance_date
            ).exists()
            
            if existing_attendance:
                messages.error(request, f"Attendance for {attendance_date} has already been marked")
                return redirect('mark_attendance')
            
            for student in students:
                status = request.POST.get(f'status_{student.roll_no}', 'Absent')
                Attendance.objects.create(
                    roll_no=student,
                    course_name=course,
                    attendance_date=attendance_date,
                    status=status,
                    marked_by=teacher
                )
            
            messages.success(request, "Attendance marked successfully")
            return redirect('teacher_dashboard')
            
        except Course.DoesNotExist:
            messages.error(request, "Invalid course selected")
        except ValueError:
            messages.error(request, "Invalid date format")
    
    context = {
        'courses': courses,
        'students': students,
        'today': today,
        'selected_course': selected_course
    }
    return render(request, 'mark_attendance.html', context)






# View Reports
# Updated View for Reports with CSV Export Feature
def view_reports(request):
    if 'teacher_username' not in request.session:
        return redirect('teacher_login')
    
    username = request.session['teacher_username']
    teacher = Teacher.objects.get(username=username)
    courses = Course.objects.filter(teacher=teacher)
    records = []
    low_attendance_students = []
    
    if request.GET:
        course_name = request.GET.get('course_name')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        if course_name:
            try:
                course = Course.objects.get(course_name=course_name, teacher=teacher)
                filters = Q(course_name=course)
                
                if from_date:
                    filters &= Q(attendance_date__gte=from_date)
                if to_date:
                    filters &= Q(attendance_date__lte=to_date)
                
                # Get all attendance records for the course
                attendances = Attendance.objects.filter(filters)
                
                # Calculate attendance percentage for each student
                student_attendance = {}
                total_classes = attendances.values('attendance_date').distinct().count()
                
                for att in attendances:
                    if att.roll_no not in student_attendance:
                        student_attendance[att.roll_no] = {
                            'name': att.roll_no.name,
                            'roll_no': att.roll_no.roll_no,
                            'total_points': 0,
                            'total_classes': total_classes,
                            'percentage': 0
                        }
                    
                    # Calculate points based on attendance status
                    if att.status == 'Present':
                        student_attendance[att.roll_no]['total_points'] += 1
                    elif att.status == 'Late':
                        student_attendance[att.roll_no]['total_points'] += 0.5
                
                # Calculate percentage for each student
                for student_data in student_attendance.values():
                    if student_data['total_classes'] > 0:
                        student_data['percentage'] = (student_data['total_points'] / student_data['total_classes']) * 100
                    
                    # Add to records for display
                    records.append({
                        'roll_no': student_data['roll_no'],
                        'name': student_data['name'],
                        'total_classes': student_data['total_classes'],
                        'total_points': student_data['total_points'],
                        'percentage': round(student_data['percentage'], 2)
                    })
                    
                    # Add to low attendance list if percentage < 75%
                    if student_data['percentage'] < 75:
                        low_attendance_students.append({
                            'roll_no': student_data['roll_no'],
                            'name': student_data['name'],
                            'percentage': round(student_data['percentage'], 2)
                        })
                
            except Course.DoesNotExist:
                messages.error(request, "Invalid course selected")
    
    # Handle CSV download
    if request.GET.get('download_csv') == 'true':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Roll No', 'Name', 'Total Classes', 'Total Points', 'Attendance %'])
        
        for record in records:
            writer.writerow([
                record['roll_no'],
                record['name'],
                record['total_classes'],
                record['total_points'],
                f"{record['percentage']}%"
            ])
        
        return response
    
    context = {
        'courses': courses,
        'records': records,
        'low_attendance_students': low_attendance_students
    }
    return render(request, 'view_reports.html', context)






# Admin Dashboard Placeholder
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')



# Logout

def logout_view(request):
    if 'teacher_username' in request.session:
        del request.session['teacher_username']
        del request.session['teacher_name']
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect('home')
