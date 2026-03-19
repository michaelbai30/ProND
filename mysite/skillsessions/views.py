# TODO - delete session as host

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from accounts.models import Skill
from .models import Session, SessionMembership
from .forms import SessionForm


@login_required
def session_list(request): # main page - list session upcoming in chronological order
    sessions = Session.objects.filter(
        date_time__gte=timezone.now()
    ).order_by('date_time').select_related('skill', 'host')
    return render(request, 'sessions/session_list.html', {
        'sessions': sessions,
    })


@login_required
def session_create(request): # create own session page - select own skill from dropdown, fill in attributes. requires 1+ skill to exist with Profile (add ability to create on the spot?)
    user_skills = Skill.objects.filter(owner=request.user)
    if not user_skills.exists():
        messages.warning(request, 'You must add a Skill before creating a Session.')
        return redirect('profile_edit')

    if request.method == 'POST':
        form = SessionForm(request.POST)
        form.fields['skill'].queryset = user_skills
        if form.is_valid():
            session = form.save(commit=False)
            session.host = request.user
            session.save()
            messages.success(request, f'Session "{session.title}" created.')
            return redirect('session_detail', pk=session.pk)
    else:
        form = SessionForm()
        form.fields['skill'].queryset = user_skills

    return render(request, 'sessions/session_create.html', {'form': form})


@login_required
def session_detail(request, pk): # view session details. conditional buttons based on host/member/joinable
    session = get_object_or_404(
        Session.objects.select_related('skill', 'host'),
        pk=pk
    )
    memberships = session.memberships.select_related('user')
    membership_count = memberships.count()

    is_host = request.user == session.host
    is_member = memberships.filter(user=request.user).exists()
    is_full = membership_count >= session.capacity
    is_past = session.date_time < timezone.now()

    return render(request, 'sessions/session_detail.html', {
        'session': session,
        'memberships': memberships,
        'membership_count': membership_count,
        'is_host': is_host,
        'is_member': is_member,
        'is_full': is_full,
        'is_past': is_past,
    })


@login_required
def session_join(request, pk): # POST only - join session if not host, not already joined, not full, current
    session = get_object_or_404(Session, pk=pk)

    if request.method != 'POST':
        return redirect('session_detail', pk=pk)

    if request.user == session.host:
        messages.error(request, 'You cannot join your own session.')
        return redirect('session_detail', pk=pk)

    if session.date_time < timezone.now():
        messages.error(request, 'This session has already passed.')
        return redirect('session_detail', pk=pk)

    with transaction.atomic():
        membership_count = session.memberships.count()
        if membership_count >= session.capacity:
            messages.error(request, 'This session is full.')
            return redirect('session_detail', pk=pk)

        if session.memberships.filter(user=request.user).exists():
            messages.info(request, 'You are already a member of this session.')
            return redirect('session_detail', pk=pk)

        SessionMembership.objects.create(session=session, user=request.user)

    messages.success(request, f'You joined "{session.title}".')
    return redirect('session_detail', pk=pk)


@login_required
def session_leave(request, pk): # POST only - leave session as member
    session = get_object_or_404(Session, pk=pk)

    if request.method != 'POST':
        return redirect('session_detail', pk=pk)

    membership = session.memberships.filter(user=request.user).first()
    if membership:
        membership.delete()
        messages.success(request, f'You left "{session.title}".')
    else:
        messages.info(request, 'You are not a member of this session.')

    return redirect('session_detail', pk=pk)
