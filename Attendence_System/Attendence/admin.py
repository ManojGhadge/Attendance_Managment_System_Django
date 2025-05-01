# from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Admin, Teacher, Student, Course, StudentCourse, Attendance
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('username', 'teacher_name', 'email')
    search_fields = ('username', 'teacher_name', 'email')
    
    def save_model(self, request, obj, form, change):
        # If password is being set or changed
        if 'password' in form.changed_data:
            obj.password = make_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'course_name', 'attendance_date', 'status', 'marked_by')
    list_filter = ('status', 'attendance_date', 'course_name', 'marked_by')
    search_fields = ('roll_no__roll_no', 'roll_no__name', 'course_name__course_name', 'marked_by__teacher_name')
    date_hierarchy = 'attendance_date'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj:  # Only for new records
            form.base_fields['marked_at'].initial = timezone.now()
        return form

# Registering models with Django admin panel
admin.site.register(Admin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(StudentCourse)
admin.site.register(Attendance, AttendanceAdmin)
