from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from ..models import Team, Member
from ..old_views import MemberViewSet
from ..serializers import TeamSerializer, MemberSerializer

import datetime

User = get_user_model()

user_dict = dict(
    username="org.sicmundus.adam",
    email="adam@sicmundus.org",
    first_name="Jonas",
    last_name="Kahnwald",
)

admin_dict = dict(
    username="gov.wnpp.Claudia",
    email="Claudia@wnpp.gov",
    first_name="Claudia",
    last_name="Tiedemann",
)

team_dict = {"name": "bugslotics", "description": "a pretty cool team"}

"""
each test validates basic CRUD functionality
"""


class TeamBaseBehavior(TestCase):
    def setUp(self):
        self.client = APIClient()

        response = self.client.post(
            reverse("rest_register"),
            {
                "username": "sschmidt",
                "password1": "p@ssw0rd90",
                "password2": "p@ssw0rd90",
                "email": "sadschmi@test.com",
            },
        )

        # if team creation fails, then all other tests will fail

        response = self.client.post(
            reverse("team-create-record"),
            team_dict,
            format="json"
        )

        for k, v in team_dict.items():
            self.assertEqual(v, response.data.get(k))

        self.team = Team.objects.get(pk=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(User.objects.count(), 0)

    def testTeamRead(self):

        response = self.client.get(
            reverse("team-detail", kwargs={"pk": self.team.id}), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in team_dict.items():
            self.assertEqual(v, response.data.get(k))

    def testTeamUpdate(self):

        updated_data = {"description": "a very cool team"}

        response = self.client.put(
            reverse("team-detail", kwargs={"pk": self.team.id}),
            updated_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for k, v in updated_data.items():
            self.assertEqual(v, response.data.get(k))

    def testTeamDelete(self):

        old_count = Team.objects.count()

        response = self.client.delete(
            reverse("team-detail", kwargs={"pk": self.team.id})
        )

        new_count = Team.objects.count()
        print(response.data)

        self.assertGreater(old_count, new_count)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MemberTeamIntegration(TestCase):
    def setUp(self):
        test_dict = {
            "username": "org.sicmundus.adam",
            "email": "adam@sicmundus.org",
            "first_name": "Jonas",
            "last_name": "Kahnwald",
        }

        self.admin = User.objects.create_user(**test_dict)
        self.admin.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("team-create-record"),
            team_dict,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.team_id = response.data["id"]

        print(self.team_id)

    def testTeam(self):
        user = dict(
            username="com.world",
            email="hello@world.com",
            first_name="hello",
            last_name="world"
        )
        self.user = User.objects.create_user(**user)
        self.user.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("member-create-record"),
            {"team_id": self.team_id, "role": "AD", "bio": "cool dude"},
            format="json"
        )
        member_id = response.data["id"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        client = APIClient()
        client.force_authenticate(user=self.admin)

        response = client.patch(
            reverse("member-approve", kwargs={"pk": member_id}), format="json"
        )

        print(response.data)

        response = client.patch(
            reverse("member-make-admin", kwargs={"pk": member_id}), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(
            reverse("member-list-team", kwargs={"pk": self.team_id}), format="json"
        )

        print(response.data)

    def testDummy(self):
        pass


class MemberBaseBehavior(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**user_dict)
        self.user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        member_data = {"team": self.team, "role": "AD", "bio": "cool dude", "owner": self.user}
        self.member = Member.objects.create(**member_data)

        self.member_id = self.member.id

    def testMemberCreate(self):
        # create a new record. this call should return the newly created record
        record = Member.objects.get(id=self.member_id)
        self.assertEqual(Member.objects.count(), 1)

    def testMemberRead(self):
        # read the record created in setUp. confirm the results are expected
        response = self.client.get(
            reverse("member-detail", kwargs={"pk": self.member_id}), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testMemberUpdate(self):
        # change the record's values. this call should return the newly updated record
        new_data = {
            "bio": "no longer a cool dude",
            "user": {"first_name": "Robert", "last_name": "Sutton"},
        }

        response = self.client.put(
            reverse("member-detail", kwargs={"pk": self.member_id}),
            new_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testMemberApproval(self):
        response = self.client.patch(
            reverse("member-approve", kwargs={"pk": self.member_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testMemberMakeAdmin(self):
        # create a admin user
        user = User.objects.create_user(**admin_dict)
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)

        member_data = {"team_id": self.team.id, "bio": "cool dude"}

        response = client.post(
            reverse("member-create-record"), member_data, format="json"
        )

        id = response.data["id"]

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("member-make-admin", kwargs={"pk": id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testMemberDelete(self):
        response = self.client.patch(
            reverse("member-leave", kwargs={"pk": self.member_id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UnauthenticatedBehavior(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**user_dict)
        self.user.save()

        self.team = Team.objects.create(**team_dict)
        self.team.save()

        self.member_data = {"team_id": self.team.id, "role": "AD", "bio": "cool dude"}

        self.client = APIClient()

        response = self.client.post(
            reverse("member-list"), self.member_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testUnauthenticated(self):
        pass
