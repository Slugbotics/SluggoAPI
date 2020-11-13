from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from ..models import Ticket
from ..models import Member
from ..models import Team, Member
from ..views import TicketViewSet

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


class TicketTestCase(TestCase):
    """This class defines the test suite for the ticket model"""

    def setUp(self):
        """ Create two test users Jonas and Noah and a ticket assigned to/created from them"""
        self.ticket_user = User.objects.create_user(**user_dict)
        self.ticket_user.save()

        self.assigned_user = User.objects.create_user(**assigned_dict)
        self.assigned_user.save()

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        self.member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        self.ticket_client = APIClient()
        self.ticket_client.force_authenticate(user=self.ticket_user)
        response = self.ticket_client.post(
            reverse("member-create-record"), self.member_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.ticket_name = "Testing Ticket"
        self.ticket_description = "Ticket used for testing"

        self.ticket = Ticket(
            owner=self.ticket_user,
            assigned_user=self.assigned_user,
            title=self.ticket_name,
            ticket_number=1,
            team=self.team,
        )

    def test_model_can_create_ticket(self):
        """ Test whether it can create a ticket"""
        old_count = Ticket.objects.count()
        self.ticket.save()
        new_count = Ticket.objects.count()
        self.assertNotEqual(old_count, new_count)

    def test_ticket_returns_readable_representation(self):
        """Tests that a readable string is represented for the models instance"""
        self.assertEqual(str(self.ticket), f"Ticket: {self.ticket_name}")


class TicketViewTestCase(TestCase):
    """ Test suite for ticket views."""

    def setUp(self):
        """ Sets up whatever is necessary for views"""
        self.ticket_user = User.objects.create_user(**user_dict)
        self.ticket_user.save()

        self.assigned_user = User.objects.create_user(**assigned_dict)
        self.assigned_user.save()

        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        self.member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        self.admin_data = {"team_id": self.team.id, "role": "AD", "bio": "cool dude"}

        self.ticket_client = APIClient()
        self.ticket_client.force_authenticate(user=self.ticket_user)
        mem_response = self.ticket_client.post(
            reverse("member-create-record"), self.member_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.assigned_client = APIClient()
        self.assigned_client.force_authenticate(user=self.assigned_user)
        mem_response = self.assigned_client.post(
            reverse("member-create-record"), self.member_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        mem_response = self.admin_client.post(
            reverse("member-create-record"), self.admin_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.ticket_data = {
            "assigned_id": self.assigned_user.id,
            "title": "Sic Mundus Creatus Est",
            "ticket_number": 1,
            "team_id": self.team.id,
        }
        self.ticket_get_data = {
            "title": "Sic Mundus Creatus Est",
            "ticket_number": 1,
            "team_id": self.team.id,
        }
        self.response = self.ticket_client.post(
            reverse("ticket-create-record"), self.ticket_data, format="json"
        )

        self.ticket_id = self.response.data["id"]

    def testTicketCreate(self):
        """Test if the api can create a ticket."""
        record = Ticket.objects.get(id=self.ticket_id)
        self.assertEqual(Ticket.objects.count(), 1)

    def testTicketRead(self):
        # read the record created in setUp. confirm the results are expected
        response = self.ticket_client.get(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in self.ticket_get_data.items():
            self.assertEqual(v, response.data.get(k))

    def testTicketUpdate(self):
        # change the record's values. this call should return the newly updated record
        new_data = {
            "title": "Erit Lux",
            "ticket_number": 2,
        }

        response = self.ticket_client.put(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}),
            new_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in new_data.items():
            self.assertEqual(v, response.data.get(k))

    def testTicketUpdateNotSignedIn(self):
        """ Test that users not signed in can't edit tickets"""
        new_data = {
            "title": "Erit Lux",
            "ticket_number": 2,
        }

        client = APIClient()
        response = client.put(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}),
            new_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testTicketUpdateNotMember(self):
        """ Test that users not signed in can't edit tickets"""
        new_data = {
            "title": "Erit Lux",
            "ticket_number": 2,
        }
        not_member = User.objects.create_user(**not_assigned_dict)
        not_member.save()

        client = APIClient()

        client.force_authenticate(user=not_member)
        response = client.put(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}),
            new_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testTicketUpdateNotOwner(self):
        """ Test that only the owner can edit tickets"""
        new_data = {
            "title": "Erit Lux",
            "ticket_number": 2,
        }
        not_user = User.objects.create_user(**not_assigned_dict)
        not_user.save()

        member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        client = APIClient()
        client.force_authenticate(user=not_user)
        mem_response = client.post(
            reverse("member-create-record"), member_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)
        response = client.put(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}),
            new_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testTicketUpdateAuth(self):
        """ Test that admins have override ability to edit tickets"""
        change_ticket = {
            "assigned_id": self.assigned_user.id,
            "title": "It's Happening Again",
            "ticket_number": 2,
        }
        response = self.admin_client.put(
            reverse("ticket-detail", kwargs={"pk": self.ticket_id}),
            change_ticket,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testTicketDeleteAuth(self):
        """ Test that admins/owners can delete ticket"""
        ticket = Ticket.objects.get(id=1)
        response = self.admin_client.delete(
            reverse("ticket-detail", kwargs={"pk": ticket.id}),
            format="json",
            follow=True,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testTicketDeleteNoAuth(self):
        """ Test that not logged in users can't delete ticket"""
        ticket = Ticket.objects.get(id=1)
        client = APIClient()
        response = client.delete(
            reverse("ticket-detail", kwargs={"pk": ticket.id}),
            format="json",
            follow=True,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testTicketDeleteNotOwner(self):

        not_user = User.objects.create_user(**not_assigned_dict)
        not_user.save()

        member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        client = APIClient()
        client.force_authenticate(user=not_user)
        mem_response = client.post(
            reverse("member-create-record"), member_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)
        ticket = Ticket.objects.get(id=1)
        response = client.delete(
            reverse("ticket-detail", kwargs={"pk": ticket.id}),
            format="json",
            follow=True,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

