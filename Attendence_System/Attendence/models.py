#from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.utils import timezone

class Admin(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Administrator"
        verbose_name_plural = "Administrators"

class Teacher(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    teacher_name = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # If the password is not hashed (length < 50), hash it
        if len(self.password) < 50:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def get_courses(self):
        return self.course_set.all()

    def get_students(self):
        return Student.objects.filter(studentcourse__course_name__teacher=self).distinct()

    def __str__(self):
        return self.teacher_name

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

class Student(models.Model):
    roll_no = models.CharField(max_length=10, primary_key=True)
    prn = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=50)
    batch = models.CharField(max_length=5)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_courses(self):
        return Course.objects.filter(studentcourse__roll_no=self)

    def get_attendance_percentage(self, course):
        total_classes = Attendance.objects.filter(
            roll_no=self,
            course_name=course
        ).count()
        
        if total_classes == 0:
            return 0
            
        present_classes = Attendance.objects.filter(
            roll_no=self,
            course_name=course,
            status='Present'
        ).count()
        
        return (present_classes / total_classes) * 100

    def __str__(self):
        return f"{self.name} ({self.roll_no})"

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

class Course(models.Model):
    course_name = models.CharField(max_length=50, primary_key=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_students(self):
        return Student.objects.filter(studentcourse__course_name=self)

    def get_attendance_stats(self):
        total_students = self.get_students().count()
        if total_students == 0:
            return {'present': 0, 'absent': 0, 'total': 0}
            
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            course_name=self,
            attendance_date=today
        )
        
        present = attendance.filter(status='Present').count()
        absent = attendance.filter(status='Absent').count()
        
        return {
            'present': present,
            'absent': absent,
            'total': total_students
        }

    def __str__(self):
        return self.course_name

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

class StudentCourse(models.Model):
    roll_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('roll_no', 'course_name')
        verbose_name = "Student Course"
        verbose_name_plural = "Student Courses"

    def __str__(self):
        return f"{self.roll_no} - {self.course_name}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Absent', 'Absent')
    ]

    roll_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)
    attendance_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_at = models.DateTimeField(default=timezone.now)
    marked_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        if self.attendance_date > timezone.now().date():
            raise ValidationError("Attendance date cannot be in the future")
        if self.attendance_date < self.course_name.created_at.date():
            raise ValidationError("Attendance date cannot be before course creation date")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('roll_no', 'course_name', 'attendance_date')
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.roll_no} - {self.course_name} - {self.attendance_date} - {self.status}"

# Login Forms will be separated in templates as admin_login.html and teacher_login.html
