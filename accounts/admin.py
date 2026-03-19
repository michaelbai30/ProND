from django.contrib import admin
from .models import Profile, Skill


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    readonly_fields = ('created_at',)
