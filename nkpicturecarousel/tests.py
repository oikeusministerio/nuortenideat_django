# coding: utf-8

from __future__ import unicode_literals

import os

from django.test import TestCase

from account.factories import UserFactory, DEFAULT_PASSWORD
from nkpicturecarousel.models import PictureCarouselImage, PictureCarouselSet
from nuka.test.testcases import TestCase as NukaTestCase


login_url = "/fi/admin/login/"
changelist_url = "/fi/admin/nkpicturecarousel/picturecarouselset/"
add_url = "/fi/admin/nkpicturecarousel/picturecarouselset/add/"


class CarouselAdminPanelTest(NukaTestCase):
    def test_open_as_superuser(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get(changelist_url)
        self.assertContains(resp, "Valitse muokattava kuvakarusellin kuva")

    def test_open_as_staff(self):
        user = UserFactory(is_staff=True)
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get(changelist_url)
        self.assertEqual(resp.status_code, 403)

    def test_open_as_normal_user(self):
        user = UserFactory()
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.get(changelist_url, follow=True)
        self.assertRedirects(
            resp, "{}?next={}".format(login_url, changelist_url),
            status_code=302, target_status_code=200
        )


class AdminUploadTest(NukaTestCase):
    def setUp(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        self.test_files = {
            "original": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'nkpicturecarousel', 'testdata', "original.jpg"
            ),
            "large": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'nkpicturecarousel', 'testdata', "large.jpg"
            ),
            "small": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'nkpicturecarousel', 'testdata', "small.jpg"
            ),
        }
        self.data = {
            "name": "Carousel Pictures",
            "is_active": "on",

            "images-0-id": "",
            "images-0-carousel_set": None,
            "images-0-language": "fi",
            "images-0-original": open(self.test_files["original"], "rb"),
            "images-0-alt_text": "First picture alt",

            "images-1-id": "",
            "images-1-carousel_set": None,
            "images-1-language": "sv",
            "images-1-original": open(self.test_files["original"], "rb"),
            "images-1-alt_text": "Second picture alt",

            # Form metadata.
            "images-TOTAL_FORMS": 2,
            "images-INITIAL_FORMS": 0,
            "images-MIN_NUM_FORMS": 1,
            "images-MAX_NUM_FORMS": 2,
        }

    def test_upload_multiple_languages(self):
        resp = self.client.post(add_url, self.data, follow=True)
        self.assertRedirects(
            resp, changelist_url, status_code=302, target_status_code=200
        )
        self.assertContains(
            resp, "Kuvakarusellin kuva &quot;Carousel Pictures&quot; on lisätty."
        )

        picture_set = PictureCarouselSet.objects.first()
        self.assertIsNotNone(picture_set)
        self.assertEqual(picture_set.name, "Carousel Pictures")
        self.assertTrue(picture_set.is_active)
        self.assertEqual(picture_set.images.all().count(), 2)

        image_1 = picture_set.images.first()
        self.assertIsNotNone(image_1)
        self.assertEqual(image_1.language, "fi")
        self.assertTrue(image_1.original.url.endswith(".jpg"))
        self.assertEqual(image_1.alt_text, "First picture alt")

        image_2 = picture_set.images.last()
        self.assertIsNotNone(image_2)
        self.assertEqual(image_2.language, "sv")
        self.assertTrue(image_2.original.url.endswith(".jpg"))
        self.assertEqual(image_2.alt_text, "Second picture alt")

        image_1.original.delete()
        image_2.original.delete()

    def test_upload_single_language(self):
        self.data["images-1-language"] = "fi"
        del self.data["images-1-original"]
        del self.data["images-1-alt_text"]

        resp = self.client.post(add_url, self.data, follow=True)
        self.assertRedirects(
            resp, changelist_url, status_code=302, target_status_code=200
        )
        self.assertContains(
            resp, "Kuvakarusellin kuva &quot;Carousel Pictures&quot; on lisätty."
        )

        picture_set = PictureCarouselSet.objects.first()
        self.assertIsNotNone(picture_set)
        self.assertEqual(picture_set.name, "Carousel Pictures")
        self.assertTrue(picture_set.is_active)
        self.assertEqual(picture_set.images.all().count(), 1)

        image_1 = picture_set.images.first()
        self.assertIsNotNone(image_1)
        self.assertEqual(image_1.language, "fi")
        self.assertTrue(image_1.original.url.endswith(".jpg"))
        self.assertEqual(image_1.alt_text, "First picture alt")

        image_1.original.delete()

    def test_missing_fields(self):
        del self.data["name"]
        del self.data["images-0-original"]
        del self.data["images-0-alt_text"]

        resp = self.client.post(add_url, self.data)
        self.assertContains(resp, "Korjaa allaolevat virheet.")
        self.assertContains(resp, "Tämä kenttä vaaditaan.", count=3)

    def test_upload_wrong_size(self):
        self.data["images-0-original"] = open(
            self.test_files["small"], "rb"
        )

        resp = self.client.post(add_url, self.data)
        self.assertContains(resp, "Korjaa allaolevat virheet.")
        self.assertContains(
            resp, "Kuvan korkeus tai leveys on liian pieni.", count=1
        )

    def test_upload_duplicate_language(self):
        self.data["images-0-language"] = "sv"
        self.data["images-1-language"] = "sv"

        resp = self.client.post(add_url, self.data)
        self.assertContains(resp, "Korjaa allaolevat virheet.")
        self.assertContains(
            resp, "Et voi ladata kahta kieliversiota samasta kielestä.", count=2
        )


class FrontpageCarouselTest(NukaTestCase):
    # TODO: Tests for other languages.

    def test_with_uploaded_pictures(self):
        test_files = {
            "original": os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'nkpicturecarousel', 'testdata', "original.jpg"
            ),
        }
        data = {
            "name": "Carousel Pictures",
            "is_active": "on",

            "images-0-id": "",
            "images-0-carousel_set": None,
            "images-0-language": "fi",
            "images-0-original": open(test_files["original"], "rb"),
            "images-0-alt_text": "Carousel picture alt-text.",

            # This image won't be uploaded.
            "images-1-id": "",
            "images-1-carousel_set": None,
            "images-1-language": "fi",

            # Form metadata.
            "images-TOTAL_FORMS": 2,
            "images-INITIAL_FORMS": 0,
            "images-MIN_NUM_FORMS": 1,
            "images-MAX_NUM_FORMS": 2,
        }

        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.login(username=user.username, password=DEFAULT_PASSWORD)
        resp = self.client.post(add_url, data, follow=True)

        self.assertRedirects(
            resp, changelist_url, status_code=302, target_status_code=200
        )
        self.assertContains(
            resp, "Kuvakarusellin kuva &quot;Carousel Pictures&quot; on lisätty."
        )

        picture_set = PictureCarouselSet.objects.first()
        self.assertIsNotNone(picture_set)
        image_1 = picture_set.images.first()
        self.assertIsNotNone(image_1)

        resp = self.client.get("/fi/")

        self.assertNotContains(resp, "/static/nuka/img/karuselli/")
        # Image has 3 size versions on the front page
        self.assertContains(resp, image_1.original.url, count=3)

        # Remember to delete the images.
        image_1.original.delete()

    def test_without_uploaded_pictures(self):
        resp = self.client.get("/fi/")
        self.assertContains(resp, "/static/nuka/img/karuselli/", count=3)
