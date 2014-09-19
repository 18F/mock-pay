from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from mock import patch

from mockpay import views


class ViewsTests(SimpleTestCase):
    @patch('mockpay.views.requests')
    def test_entry_requirements(self, requests):
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

        #   None of the tests thus far should have made an http request
        self.assertFalse(requests.post.called)

    @patch('mockpay.views.requests')
    def test_entry_requirements_valid(self, requests):
        """A successful POST from the browser should result in a POST to the
        configured url with the provided agency_/tracking_id"""
        mock_config = {"AGENCY": {"transaction_url": "exexex"}}
        with self.settings(AGENCY_CONFIG=mock_config):
            message = {'agency_id': 'AGENCY', 'agency_tracking_id': 'TRA'}
            self.client.post(reverse('entry'), message)
            self.assertTrue(requests.post.called)
            self.assertEqual(requests.post.call_args[0][0], 'exexex')
            self.assertEqual(requests.post.call_args[1]['data'], message)

    def test_lookup_config(self):
        """Fetching a key should first look in the app info and cascade up"""
        mock_config = {"AGENCY": {"key_a": "value_1", "key_b": "value_2",
                                  "apps": {"APPNAME": {"key_b": "value_3"}}}}
        with self.settings(AGENCY_CONFIG=mock_config):
            #   Agency not present in config
            self.assertEqual(views.lookup_config("key_b", "other", None),
                             None)
            #   App not present in config
            self.assertEqual(views.lookup_config("key_b", "AGENCY", "NONAPP"),
                             None)
            #   Key not present in config
            self.assertEqual(views.lookup_config("key_z", "AGENCY", "APPNAME"),
                             None)
            #   App overrides Agency setting
            self.assertEqual(views.lookup_config("key_b", "AGENCY", "APPNAME"),
                             "value_3")
            #   Falls back to Agency setting
            self.assertEqual(views.lookup_config("key_a", "AGENCY", "APPNAME"),
                             "value_1")
            self.assertEqual(views.lookup_config("key_b", "AGENCY", None),
                             "value_2")

    def test_clean_agency_response_errors(self):
        """This function should return error strings if given XML, duplicate
        keys, missing value, unknown keys, or not given a required key"""
        inputs = ["<xml>",
                  "key=value\nkey=other value",
                  "unexplained string",
                  "key=   ",
                  "action=value\npayment_type=value",
                  "protocol_version=1\nresponse_message=2\naction=3\n"
                  + "form_id=4\nagency_tracking_id=5\nother_key=6"]
        responses = set()
        for response_str in inputs:
            clean = views.clean_agency_response(response_str)
            self.assertTrue(isinstance(clean, str))
            responses.add(clean)
        # they should all have provided different error messages
        self.assertEqual(len(responses), len(inputs))

    def test_clean_agency_response(self):
        """Example of a successful input-string-to-dictionary conversion as
        all required (and some optional) fields are present. Tests various
        line endings"""
        input_str = ("action=SubmitCollectionInteractive\n"
                     + "payment_amount=20.25\r\n"
                     + "form_id=123\r"
                     + "payer_name=Bob Smith\n"
                     + "agency_tracking_id=090909\n"
                     + "protocol_version=3.2\n"
                     + "response_message=Success")
        clean = views.clean_agency_response(input_str)
        self.assertEqual(clean, {
            "action": "SubmitCollectionInteractive",
            "payment_amount": "20.25",
            "form_id": "123",
            "payer_name": "Bob Smith",
            "agency_tracking_id": "090909",
            "protocol_version": "3.2",
            "response_message": "Success"
        })

    def test_generate_form_no_form(self):
        """The form is looked up; if it's not present, we get an error"""
        with self.settings(FORM_CONFIGS={"111": []}):
            response = views.generate_form(None, {"form_id": "2222"})
            self.assertEqual(response.status_code, 400)

    def test_generate_form(self):
        """The generated form should include only fields in the form config"""
        config = {"111": [{"name": "field1", "status": "editable"},
                          {"name": "field2", "status": "locked"},
                          {"name": "field3", "status": "hidden"}]}
        params = {"form_id": "111", "field2": "value2", "field4": "value4"}
        with self.settings(FORM_CONFIGS=config):
            response = views.generate_form(None, params)
            self.assertContains(response, "field1")
            self.assertContains(response, "field2")
            self.assertContains(response, "field3")
            self.assertContains(response, "value2")
            self.assertNotContains(response, "field4")
            self.assertNotContains(response, "value4")
