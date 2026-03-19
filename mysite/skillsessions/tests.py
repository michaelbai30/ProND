# AI gen tests. add/edit/delete as needed

from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from accounts.models import Skill
from .models import Session, SessionMembership


class SessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='host', password='testpass123')
        self.skill = Skill.objects.create(owner=self.user, name='Python')

    def test_create_session(self):
        session = Session.objects.create(
            skill=self.skill,
            host=self.user,
            title='Python Basics',
            description='Intro to Python',
            location='Room 101',
            date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            capacity=10,
        )
        self.assertEqual(session.host, self.user)
        self.assertEqual(session.skill, self.skill)
        self.assertIsNotNone(session.created_at)

    def test_session_str(self):
        session = Session.objects.create(
            skill=self.skill,
            host=self.user,
            title='Python Basics',
            location='Room 101',
            date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            capacity=10,
        )
        self.assertEqual(str(session), 'Python Basics (Python)')

    def test_clean_rejects_mismatched_host_and_skill_owner(self):
        other_user = User.objects.create_user(username='other', password='testpass123')
        session = Session(
            skill=self.skill,
            host=other_user,
            title='Stolen Session',
            location='Room 101',
            date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            capacity=10,
        )
        with self.assertRaises(ValidationError):
            session.clean()

    def test_clean_accepts_matching_host_and_skill_owner(self):
        session = Session(
            skill=self.skill,
            host=self.user,
            title='Valid Session',
            location='Room 101',
            date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            capacity=10,
        )
        session.clean()  # should not raise


class SessionMembershipModelTest(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='host', password='testpass123')
        self.learner = User.objects.create_user(username='learner', password='testpass123')
        self.skill = Skill.objects.create(owner=self.host, name='Python')
        self.session = Session.objects.create(
            skill=self.skill,
            host=self.host,
            title='Python Basics',
            location='Room 101',
            date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            capacity=10,
        )

    def test_create_membership(self):
        membership = SessionMembership.objects.create(
            session=self.session,
            user=self.learner,
        )
        self.assertEqual(membership.session, self.session)
        self.assertEqual(membership.user, self.learner)
        self.assertIsNotNone(membership.joined_at)

    def test_membership_str(self):
        membership = SessionMembership.objects.create(
            session=self.session,
            user=self.learner,
        )
        self.assertEqual(str(membership), 'learner in Python Basics')

    def test_duplicate_membership_rejected(self):
        SessionMembership.objects.create(session=self.session, user=self.learner)
        with self.assertRaises(IntegrityError):
            SessionMembership.objects.create(session=self.session, user=self.learner)

    def test_same_user_different_sessions_allowed(self):
        other_session = Session.objects.create(
            skill=self.skill,
            host=self.host,
            title='Python Advanced',
            location='Room 102',
            date_time=timezone.now() + timedelta(days=2),
            duration_minutes=60,
            capacity=5,
        )
        SessionMembership.objects.create(session=self.session, user=self.learner)
        SessionMembership.objects.create(session=other_session, user=self.learner)
        self.assertEqual(SessionMembership.objects.filter(user=self.learner).count(), 2)


class SessionListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.skill = Skill.objects.create(owner=self.user, name='Python')

    def test_session_list_requires_login(self):
        response = self.client.get(reverse('session_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_session_list_shows_future_sessions_only(self):
        self.client.login(username='testuser', password='testpass123')
        Session.objects.create(
            skill=self.skill, host=self.user, title='Future',
            location='Room 1', date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60, capacity=5,
        )
        Session.objects.create(
            skill=self.skill, host=self.user, title='Past',
            location='Room 2', date_time=timezone.now() - timedelta(days=1),
            duration_minutes=60, capacity=5,
        )
        response = self.client.get(reverse('session_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future')
        self.assertNotContains(response, 'Past')


class SessionCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_session_create_requires_login(self):
        response = self.client.get(reverse('session_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_session_create_redirects_if_no_skills(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('session_create'))
        self.assertRedirects(response, reverse('profile_edit'))

    def test_session_create_success(self):
        self.client.login(username='testuser', password='testpass123')
        skill = Skill.objects.create(owner=self.user, name='Python')
        response = self.client.post(reverse('session_create'), {
            'skill': skill.id,
            'title': 'Python Basics',
            'description': 'Learn Python',
            'location': 'Room 101',
            'date_time': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'duration_minutes': 60,
            'capacity': 10,
        })
        self.assertEqual(Session.objects.count(), 1)
        session = Session.objects.first()
        self.assertEqual(session.host, self.user)
        self.assertEqual(session.title, 'Python Basics')


class SessionDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='testpass123')
        self.learner = User.objects.create_user(username='learner', password='testpass123')
        self.skill = Skill.objects.create(owner=self.host, name='Python')
        self.session = Session.objects.create(
            skill=self.skill, host=self.host, title='Python Basics',
            location='Room 101', date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60, capacity=2,
        )

    def test_session_detail_requires_login(self):
        response = self.client.get(reverse('session_detail', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_session_detail_context_for_host(self):
        self.client.login(username='host', password='testpass123')
        response = self.client.get(reverse('session_detail', args=[self.session.pk]))
        self.assertTrue(response.context['is_host'])
        self.assertFalse(response.context['is_member'])

    def test_session_detail_context_for_member(self):
        self.client.login(username='learner', password='testpass123')
        SessionMembership.objects.create(session=self.session, user=self.learner)
        response = self.client.get(reverse('session_detail', args=[self.session.pk]))
        self.assertFalse(response.context['is_host'])
        self.assertTrue(response.context['is_member'])

    def test_session_detail_context_full(self):
        self.client.login(username='learner', password='testpass123')
        user_a = User.objects.create_user(username='a', password='testpass123')
        user_b = User.objects.create_user(username='b', password='testpass123')
        SessionMembership.objects.create(session=self.session, user=user_a)
        SessionMembership.objects.create(session=self.session, user=user_b)
        response = self.client.get(reverse('session_detail', args=[self.session.pk]))
        self.assertTrue(response.context['is_full'])


class SessionJoinViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='testpass123')
        self.learner = User.objects.create_user(username='learner', password='testpass123')
        self.skill = Skill.objects.create(owner=self.host, name='Python')
        self.session = Session.objects.create(
            skill=self.skill, host=self.host, title='Python Basics',
            location='Room 101', date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60, capacity=2,
        )

    def test_join_session_success(self):
        self.client.login(username='learner', password='testpass123')
        response = self.client.post(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).exists())

    def test_join_via_get_redirects_without_joining(self):
        self.client.login(username='learner', password='testpass123')
        response = self.client.get(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).exists())

    def test_join_own_session_rejected(self):
        self.client.login(username='host', password='testpass123')
        response = self.client.post(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessionMembership.objects.filter(
            session=self.session, user=self.host
        ).exists())

    def test_join_full_session_rejected(self):
        self.client.login(username='learner', password='testpass123')
        user_a = User.objects.create_user(username='a', password='testpass123')
        user_b = User.objects.create_user(username='b', password='testpass123')
        SessionMembership.objects.create(session=self.session, user=user_a)
        SessionMembership.objects.create(session=self.session, user=user_b)
        response = self.client.post(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).exists())

    def test_join_past_session_rejected(self):
        self.client.login(username='learner', password='testpass123')
        self.session.date_time = timezone.now() - timedelta(days=1)
        self.session.save()
        response = self.client.post(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).exists())

    def test_join_already_joined_does_not_duplicate(self):
        self.client.login(username='learner', password='testpass123')
        SessionMembership.objects.create(session=self.session, user=self.learner)
        response = self.client.post(reverse('session_join', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).count(), 1)


class SessionLeaveViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='testpass123')
        self.learner = User.objects.create_user(username='learner', password='testpass123')
        self.skill = Skill.objects.create(owner=self.host, name='Python')
        self.session = Session.objects.create(
            skill=self.skill, host=self.host, title='Python Basics',
            location='Room 101', date_time=timezone.now() + timedelta(days=1),
            duration_minutes=60, capacity=5,
        )

    def test_leave_session_success(self):
        self.client.login(username='learner', password='testpass123')
        SessionMembership.objects.create(session=self.session, user=self.learner)
        response = self.client.post(reverse('session_leave', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SessionMembership.objects.filter(
            session=self.session, user=self.learner
        ).exists())

    def test_leave_when_not_a_member(self):
        self.client.login(username='learner', password='testpass123')
        response = self.client.post(reverse('session_leave', args=[self.session.pk]))
        self.assertEqual(response.status_code, 302)
