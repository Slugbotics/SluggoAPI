from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from api.models import (Ticket, Team, Member, Tag, TicketStatus, TicketTag, TicketNode)
from ..serializers import UserSerializer, TicketStatusSerializer, TicketTagSerializer

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
    """ Test suite for ticket old_views."""

    def setUp(self):
        """ Sets up whatever is necessary for old_views"""
        self.ticket_user = User.objects.create_user(**user_dict)
        self.ticket_user.save()

        self.assigned_user = User.objects.create_user(**assigned_dict)
        self.assigned_user.save()

        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.ticket_client = APIClient()
        self.ticket_client.force_authenticate(user=self.ticket_user)
        mem_response = self.ticket_client.post(
            reverse("team-create-record"), team_dict, format="json"
        )
        team_id = mem_response.data["id"]
        self.team = Team.objects.get(pk=team_id)

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.member_data = {"team_id": self.team.id, "role": "AP", "bio": "Cool Users"}

        self.admin_data = {"owner": self.admin_user, "team": self.team, "role": "AD", "bio": "cool dude"}

        self.assigned_client = APIClient()
        self.assigned_client.force_authenticate(user=self.assigned_user)
        mem_response = self.assigned_client.post(
            reverse("member-create-record"), self.member_data, format="json"
        )

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.admin_member = Member.objects.create(**self.admin_data)
        self.admin_member.save()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

        member = Member.objects.get(owner=self.admin_user)
        print(member.team_id)

        self.assertEqual(mem_response.status_code, status.HTTP_201_CREATED)

        self.ticket_data = {
            "assigned_id": self.assigned_user.id,
            "title": "Sic Mundus Creatus Est",
            "team_id": self.team.id,
        }
        self.ticket_get_data = {
            "title": "Sic Mundus Creatus Est",
            "team_id": self.team.id,
        }

        self.response = None
        for i in range(3):
            self.response = self.ticket_client.post(
                reverse("ticket-create-record"), self.ticket_data, format="json"
            )

        self.ticket_id = self.response.data["id"]
        self.ticket = Ticket.objects.get(pk=self.ticket_id)

    def testTicketCreate(self):
        """Test if the api can create a ticket."""
        record = Ticket.objects.get(id=self.ticket_id)
        self.assertEqual(Ticket.objects.count(), 3)

    def testTicketRead(self):
        # read the record created in setUp. confirm the results are expected
        url = reverse("ticket-detail", kwargs={"pk": self.ticket_id})
        response = self.ticket_client.get(
            url, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testTicketList(self):
        # eat shit and die

        self.another_ticket = {
            "title": "Ticket",
            "description": "Fix the toaster",
            "team_id": self.team.id,
        }

        self.ticket_client.post(
            reverse("ticket-create-record"),
            self.another_ticket,
            format="json"
        )

        url = reverse('ticket-list-team', kwargs={"pk": self.team.id})
        url += '?search=-created'

        print(url)

        response = self.ticket_client.get(
            url, format="json"
        )
        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testTicketUpdate(self):
        # change the record's values. this call should return the newly updated record
        new_data = {
            "title": "Erit Lux",
            "team_id": self.team.id
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
            "team_id": self.team.id,
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
            "team_id": self.team.id,
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
            "team_id": self.team.id,
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
            "team_id": self.team.id,
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

    def testCreateSubticket(self):
        subticket_data = {
            "title": "sub ticket",
            "ticket_number": 999,
            "team_id": self.team.id,
            "parent_id": self.ticket_id
        }

        response = self.admin_client.post(
            reverse("ticket-create-record"),
            subticket_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        root_node = TicketNode.objects.get(ticket=self.ticket)
        self.assertEqual(root_node.get_children_count(), 1)

    def testAddSubticket(self):
        # create a ticket to be added
        subticket_data = Ticket(
            owner=self.ticket_user,
            title="try not to cringe",
            ticket_number=1,
            team=self.team,
        )

        subticket_data.save()

        response = self.admin_client.patch(
            reverse("ticket-add-as-subticket", kwargs={"pk": subticket_data.pk}),
            {"parent_id": self.ticket_id},
            format="json"
        )

        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        root_node = TicketNode.objects.get(ticket=self.ticket)
        self.assertEqual(root_node.get_children_count(), 1)

        root_sub_data = Ticket(
            owner=self.ticket_user,
            title="oh, so you're approaching me?",
            ticket_number=123123,
            team=self.team
        )
        root_sub_data.save()
        TicketNode.add_root(ticket=root_sub_data)

        response = self.admin_client.patch(
            reverse("ticket-add-as-subticket", kwargs={"pk": root_sub_data.pk}),
            {"parent_id": self.ticket_id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        root_node = TicketNode.objects.get(ticket=self.ticket)
        self.assertEqual(root_node.get_children_count(), 2)

        existing_sub_data = {
            "title": "sub ticket",
            "ticket_number": 999,
            "team_id": self.team.id,
            "parent_id": self.ticket_id
        }

        response = self.admin_client.post(
            reverse("ticket-create-record"),
            existing_sub_data,
            format="json"
        )

        existing_id = response.data["id"]

        response = self.admin_client.patch(
            reverse("ticket-add-as-subticket", kwargs={"pk": existing_id}),
            {"parent_id": self.ticket_id},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        root_node = TicketNode.objects.get(ticket=self.ticket)
        self.assertEqual(root_node.get_children_count(), 3)

        print(TicketNode.dump_bulk())

        url = reverse("ticket-detail", kwargs={"pk": self.ticket_id})
        response = self.ticket_client.get(
            url, format="json"
        )

        children = response.data.get('children', None)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(children, None)

    def testGetOwned(self):

        response = self.ticket_client.get(
            reverse("ticket-retrieve-user-tickets"), QUERY_STRING=f'team_id={self.team.id}', format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testFilter(self):
        url = reverse("ticket-list-team", kwargs={"pk": self.team.id})
        url += f"?owner__username={self.ticket_user.username}"

        response = self.ticket_client.get(
            url,
            format="json"
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TagViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.ticket_client = APIClient()
        self.ticket_client.force_authenticate(user=self.admin_user)
        response = self.ticket_client.post(
            reverse("team-create-record"), team_dict, format="json"
        )
        self.team = Team.objects.get(pk=response.data["id"])

        tag_dict = {
            "team_id": self.team.id,
            "title": "TAG"
        }
        response = self.ticket_client.post(
            reverse("tag-create-record"), tag_dict, format="json"
        )
        self.tag = Tag.objects.get(pk=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testRead(self):
        response = self.ticket_client.get(
            reverse("tag-detail", kwargs={"pk": self.tag.id}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testUpdate(self):
        tag_dict = {
            "title": "asldkfj",
            "team_id": self.tag.team.id
        }

        response = self.ticket_client.put(
            reverse("tag-detail", kwargs={"pk": self.tag.id}),
            tag_dict,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testDelete(self):
        response = self.ticket_client.delete(
            reverse("tag-detail", kwargs={"pk": self.tag.id}),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def testTicket(self):
        ticket_data = {
            "title": "Sic Mundus Creatus Est",
            "team_id": self.team.id,
            "tag_id_list": [
                self.tag.id,
            ]
        }
        response = self.ticket_client.post(
            reverse("ticket-create-record"),
            ticket_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ticket_tag = TicketTag.objects.get(team=self.team)

        self.ticket = Ticket.objects.get(pk=response.data["id"])
        response = self.ticket_client.get(
            reverse("ticket-detail", kwargs={"pk": self.ticket.id}),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # response = self.ticket_client.get(
        #    reverse("tickettag-fetch-ticket", kwargs={"pk": self.ticket.id}),
        #    format="json"
        # )
        # print(response.data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)


class StatusViewTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.ticket_client = APIClient()
        self.ticket_client.force_authenticate(user=self.admin_user)
        response = self.ticket_client.post(
            reverse("team-create-record"), team_dict, format="json"
        )
        self.team = Team.objects.get(pk=response.data["id"])

        status_dict = {
            "team_id": self.team.id,
            "title": "IN PROGRESS"
        }
        response = self.ticket_client.post(
            reverse("ticketstatus-create-record"), status_dict, format="json"
        )
        self.status = TicketStatus.objects.get(pk=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testRead(self):
        response = self.ticket_client.get(
            reverse("ticketstatus-detail", kwargs={"pk": self.status.id}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testList(self):
        response = self.ticket_client.get(
            reverse("ticketstatus-list-team", kwargs={"pk": self.team.id}), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testUpdate(self):
        status_dict = {
            "title": "asldkfj",
            "team_id": self.status.team.id
        }

        response = self.ticket_client.put(
            reverse("ticketstatus-detail", kwargs={"pk": self.status.id}),
            status_dict,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testDelete(self):
        response = self.ticket_client.delete(
            reverse("ticketstatus-detail", kwargs={"pk": self.status.id}),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def testTicket(self):
        serialized = TicketStatusSerializer(self.status)
        ticket_data = {
            "title": "Sic Mundus Creatus Est",
            "team_id": self.team.id,
            "status_id": self.status.id
        }
        response = self.ticket_client.post(
            reverse("ticket-create-record"),
            ticket_data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testFilter(self):
        url = reverse("ticketstatus-list-team", kwargs={"pk": self.team.id})
        url += f"?title={self.status.title}"
        print(url)
        response = self.ticket_client.get(
            url,
            format="json"
        )
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TicketNodeTestCase(TestCase):
    def setUp(self):
        # the following is lifted directly from the tutorial

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        self.admin_user = User.objects.create_user(**admin_dict)
        self.admin_user.save()

        self.root_ticket_data = {
            "title": "Sic Mundus Creatus Est",
            "team": self.team,
            "owner": self.admin_user
        }
        self.root_ticket = Ticket.objects.create(**self.root_ticket_data)
        self.root_ticket.save()

        self.child_ticket_data = {
            "title": "child",
            "team": self.team,
            "owner": self.admin_user
        }
        self.child_ticket = Ticket.objects.create(**self.child_ticket_data)
        self.child_ticket.save()

        self.second_root_ticket_data = {
            "title": "other root",
            "team": self.team,
            "owner": self.admin_user
        }
        self.second_root_ticket = Ticket.objects.create(**self.second_root_ticket_data)
        self.second_root_ticket.save()

        get = lambda node_id: TicketNode.objects.get(pk=node_id)
        root = TicketNode.add_root(ticket=self.root_ticket)
        root2 = TicketNode.add_root(ticket=self.second_root_ticket)
        child = get(root.pk).add_child(ticket=self.child_ticket)

        root2.move(get(root.pk), pos="last-child")

    def testRead(self):
        print(TicketNode.dump_bulk())
