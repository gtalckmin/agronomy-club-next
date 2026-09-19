from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from agronomy_club.models import Chapter, ChapterMembership, User


class MemberAdministrationTests(TestCase):
    def setUp(self):
        self.staff_user = get_user_model().objects.create_superuser(
            username="club-admin",
            email="club-admin@example.com",
            password="not-used-in-this-test",
        )
        self.member = User.objects.create(
            full_name="Ada Lovelace",
            grad_yr=2030,
            discipline="Agronomy",
            email="ada@example.com",
        )
        self.chapter = Chapter.objects.create(
            name="Perth Chapter",
            abbrev="PER",
            location="Perth",
            desc="A chapter used to test the administration interface.",
            email="perth@example.com",
            colour="#aabbcc",
        )

    def test_member_edit_page_includes_chapter_memberships_inline(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_user_change", args=[self.member.pk])
        )

        self.assertEqual(response.status_code, 200)
        inline_models = {
            inline_admin_formset.opts.model
            for inline_admin_formset in response.context["inline_admin_formsets"]
        }
        self.assertIn(ChapterMembership, inline_models)

    def test_chapter_edit_page_includes_member_inline(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_chapter_change", args=[self.chapter.pk])
        )

        self.assertEqual(response.status_code, 200)
        inline_models = {
            inline_admin_formset.opts.model
            for inline_admin_formset in response.context["inline_admin_formsets"]
        }
        self.assertIn(ChapterMembership, inline_models)

    def test_member_list_searches_email_addresses(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_user_changelist"),
            {"q": self.member.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["cl"].result_list), [self.member])

    def test_member_edit_page_groups_profile_and_access_fields(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_user_change", args=[self.member.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Member details")
        self.assertContains(response, "Academic profile")
        self.assertContains(response, "Club access")
        self.assertContains(response, "Firebase identity")

    def test_membership_list_uses_member_and_chapter_headings(self):
        ChapterMembership.objects.create(
            user_id=self.member,
            chapter_id=self.chapter,
            position="",
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("admin:agronomy_club_chaptermembership_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "User id")
        self.assertNotContains(response, "Chapter id")

    def test_membership_list_searches_member_email_addresses(self):
        membership = ChapterMembership.objects.create(
            user_id=self.member,
            chapter_id=self.chapter,
            position="",
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_chaptermembership_changelist"),
            {"q": self.member.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["cl"].result_list), [membership])

    def test_member_list_shows_chapter_counts_without_firebase_identifiers(self):
        ChapterMembership.objects.create(
            user_id=self.member,
            chapter_id=self.chapter,
            position="",
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("admin:agronomy_club_user_changelist"))

        self.assertEqual(response.status_code, 200)
        displayed_member = response.context["cl"].result_list.get(pk=self.member.pk)
        self.assertTrue(hasattr(displayed_member, "chapter_count"))
        self.assertEqual(displayed_member.chapter_count, 1)
        self.assertContains(response, "Chapters")
        self.assertNotContains(response, "Firebase uid")

    def test_membership_list_filters_by_chapter(self):
        membership = ChapterMembership.objects.create(
            user_id=self.member,
            chapter_id=self.chapter,
            position="",
        )
        other_member = User.objects.create(
            full_name="Grace Hopper",
            grad_yr=2031,
            discipline="Soil science",
            email="grace@example.com",
        )
        other_chapter = Chapter.objects.create(
            name="Wheatbelt Chapter",
            abbrev="WHEAT",
            location="Northam",
            desc="A second chapter used to test administration filters.",
            email="wheatbelt@example.com",
            colour="#ddeeff",
        )
        ChapterMembership.objects.create(
            user_id=other_member,
            chapter_id=other_chapter,
            position="",
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("admin:agronomy_club_chaptermembership_changelist"),
            {"chapter_id__id__exact": self.chapter.pk},
        )

        self.assertEqual(response.status_code, 200)
        filter_paths = [filter_spec.field_path for filter_spec in response.context["cl"].filter_specs]
        self.assertIn("chapter_id", filter_paths)
        self.assertEqual(list(response.context["cl"].result_list), [membership])

    def test_membership_list_offers_a_position_filter(self):
        ChapterMembership.objects.create(
            user_id=self.member,
            chapter_id=self.chapter,
            chapter_role="admin",
            position="pres",
        )
        other_member = User.objects.create(
            full_name="Katherine Johnson",
            grad_yr=2031,
            discipline="Agronomy",
            email="katherine@example.com",
        )
        other_chapter = Chapter.objects.create(
            name="Great Southern Chapter",
            abbrev="GS",
            location="Albany",
            desc="A second chapter used to test committee filters.",
            email="great-southern@example.com",
            colour="#ccddff",
        )
        ChapterMembership.objects.create(
            user_id=other_member,
            chapter_id=other_chapter,
            chapter_role="admin",
            position="ocm",
        )
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("admin:agronomy_club_chaptermembership_changelist"))

        self.assertEqual(response.status_code, 200)
        filter_paths = [filter_spec.field_path for filter_spec in response.context["cl"].filter_specs]
        self.assertIn("position", filter_paths)
