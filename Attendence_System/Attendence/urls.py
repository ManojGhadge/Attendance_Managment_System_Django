# from django.urls import path
# from . import views

# urlpatterns = [
#     # Common
#   #  path('', views.home, name='home'),

#     # Admin URLs
#     path('admin/login/', views.admin_login, name='admin_login'),
#     path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
#     path('admin/add_student/', views.add_student, name='add_student'),
#     path('admin/add_teacher/', views.add_teacher, name='add_teacher'),
#     path('admin/add_course/', views.add_course, name='add_course'),
#     path('admin/view_reports/', views.view_reports, name='view_reports'),
#     path('admin/download_csv/', views.download_csv, name='download_csv'),

#     # Teacher URLs
#     path('teacher/login/', views.teacher_login, name='teacher_login'),
#     path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
#     path('teacher/mark_attendance/', views.mark_attendance, name='mark_attendance'),
#     path('teacher/view_attendance/', views.teacher_view_attendance, name='teacher_view_attendance'),

#     # Logout
#     path('logout/', views.logout_view, name='logout'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 👈 This shows the role selector homepage
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/view_reports/', views.view_reports, name='view_reports'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
