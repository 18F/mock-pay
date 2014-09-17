from django.core.urlresolvers import reverse
from django.test import SimpleTestCase


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
