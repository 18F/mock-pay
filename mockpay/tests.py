from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from mock import patch

from mockpay import views


class ViewsTests(SimpleTestCase):
    def test_entry_requirements(self):
        """Entry point only accepts POSTs, and needs two fields set"""
        response = self.client.get(reverse('entry'))
        self.assertEqual(405, response.status_code)

        message = {}
        response = self.client.post(reverse('entry'), message)
        self.assertEqual(400, response.status_code)

        message = {'agency_id': 'AGENCY'}
        response = self.client.post(reverse('entry'), message)
        self.assertEqual(400, response.status_code)

        message = {'agency_tracking_id': 'TRACKTRACK'}
        response = self.client.post(reverse('entry'), message)
        self.assertEqual(400, response.status_code)

    @patch('mockpay.views.requests')
    def test_entry_requirements_valid(self, requests):
        """A successful POST from the browser should result in a POST to the
        configured url with the provided agency_/tracking_id"""
        mock_info = {"AGENCY": {"DEFAULT": {"form_id": 1, "url": "exexex"}}}
        with self.settings(CALLBACK_INFO=mock_info):
            message = {'agency_id': 'AGENCY', 'agency_tracking_id': 'TRA'}
            response = self.client.post(reverse('entry'), message)
            self.assertEqual(200, response.status_code)
            self.assertTrue(requests.post.called)
            self.assertEqual(requests.post.call_args[0][0], 'exexex')
            self.assertEqual(requests.post.call_args[1]['data'], message)

    def test_lookup_callback_info(self):
        """We should only get callback info if the agency_id and app match, or
        there is no app"""
        mock_info = {"AGENCY": {
            "ANAPP": {"form_id": 123, "url": "http://example.com/"},
            "DEFAULT": {"form_id": 321, "url": "http://example.gov/"}
        }}
        with self.settings(CALLBACK_INFO=mock_info):
            self.assertEqual(views.lookup_callback_info("other_agency", None),
                             None)
            self.assertEqual(views.lookup_callback_info("AGENCY", "NONAPP"),
                             None)
            self.assertEqual(views.lookup_callback_info("AGENCY", "ANAPP"),
                             {"form_id": 123, "url": "http://example.com/"})
            self.assertEqual(views.lookup_callback_info("AGENCY", None),
                             {"form_id": 321, "url": "http://example.gov/"})
