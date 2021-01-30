from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from api.models import (Ticket, Team, Member, Tag, TicketStatus, TicketTag, TicketNode, Event)
from ..serializers import UserSerializer, EventSerializer

import datetime

User = get_user_model()

assigned_dict = dict(
    username="org.sicmundus.noah",
    email="noah@sicmundus.org",
    first_name="Hanno",
    last_name="Tauber",
)

user_dict = dict(
    username="org.sicmundus.adam",
    email="adam@sicmundus.org",
    first_name="Jonas",
    last_name="Kahnwald",
)

not_assigned_dict = dict(
    username="org.eritlux.eva",
    email="eva@eritlux.org",
    first_name="Martha",
    last_name="Nielsen",
)

admin_dict = dict(
    username="gov.wnpp.Claudia",
    email="Claudia@wnpp.gov",
    first_name="Claudia",
    last_name="Tiedemann",
)

team_dict = {"name": "bugslotics", "description": "a pretty cool team"}

class EventTestCase(TestCase):
    def setUp(self):
        """ Create two test users Jonas and Noah and a ticket assigned to/created from them"""
        self.event_user = User.objects.create_user(**user_dict)
        self.event_user.save()

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        self.member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        self.event_client = APIClient()
        self.event_client.force_authenticate(user=self.event_user)
        response = self.event_client.post(
            reverse("member-create-record"), self.member_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.event_description = "Event used for testing"

        self.event = Event(
            team=self.team,
            created=datetime.datetime(2020, 10, 9, 23, 55, 59, 342380),
            event_type="1",
            description=self.event_description,
            user=self.assigned_user
        )

    def test_model_can_create_event(self):
        """ Test whether it can create an event"""
        old_count = Event.objects.count()
        self.event.save()
        new_count = Event.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_event_returns_readable_representation(self):
        """Tests that a readable string is represented for the models instance"""
        self.assertEqual(str(self.event), f"Event: {self.event_type}, {self.description}")

class EventViewTestCase(TestCase):
    def setUp(self):
        self.event_user = User.objects.create_user(**user_dict)
        self.event_user.save()

        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.event_client = APIClient()
        self.event_client.force_authenticate(user=self.event_user)
        mem_response = self.ticket_client.post(
            reverse("team-create-record"), team_dict, format="json"
        )
        team_id = mem_response.data["id"]
        self.team = Team.objects.get(pk=team_id)

        self.event_data = {
            "event_id": self.event_user.id,
            "title": "Sic Mundus Creatus Est",
            "team_id": self.team.id,
        }

        self.response = None
        for i in range(3):
            self.response = self.event_client.post(
                reverse("event-create-record"), self.event_data, format="json"
            )

        self.event_id = self.response.data["id"]
        self.event = Ticket.objects.get(pk=self.ticket_id)


