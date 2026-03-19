from django.urls import path
from .views import login_page, profile_view, profile_edit, profile_detail

urlpatterns = [
    path('', login_page, name='login'),
    path('profile/', profile_view, name='profile_view'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/<int:user_id>/', profile_detail, name='profile_detail'),
]