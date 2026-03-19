from django.urls import path
from . import views

urlpatterns = [
    path('', views.session_list, name='session_list'),
    path('create/', views.session_create, name='session_create'),
    path('<int:pk>/', views.session_detail, name='session_detail'),
    path('<int:pk>/join/', views.session_join, name='session_join'),
    path('<int:pk>/leave/', views.session_leave, name='session_leave'),
]
