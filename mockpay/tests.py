from django.core.urlresolvers import reverse
from django.test import SimpleTestCase
from mock import patch

from mockpay import views, access_settings


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

    def test_agency_response_to_dict(self):
        """This function should return error strings if given XML, duplicate
        keys, or missing keys. Otherwise, we should parse a nice dictionary"""
        responses = set()

        clean = views.agency_response_to_dict("<xml>")
        self.assertTrue(isinstance(clean, str))
        responses.add(clean)

        clean = views.agency_response_to_dict("key=value\nkey=other")
        self.assertTrue(isinstance(clean, str))
        responses.add(clean)

        clean = views.agency_response_to_dict("key=")
        self.assertTrue(isinstance(clean, str))
        responses.add(clean)

        self.assertEqual(len(responses), 3)     # different error messages

        clean = views.agency_response_to_dict("key1=value1\nkey2=value2\r\n"
                                              + "key3=value3")
        self.assertEqual(clean, {"key1": "value1", "key2": "value2",
                                 "key3": "value3"})

    def test_generate_form_no_form(self):
        """The form is looked up; if it's not present, we get an error"""
        with self.settings(FORM_CONFIGS={"111": []}):
            response = views.generate_form(None, None, None,
                                           {"form_id": "2222"})
            self.assertEqual(response.status_code, 400)

    def test_generate_form(self):
        """The generated form should include only fields in the form config"""
        config = {"111": [{"name": "field1", "status": "editable"},
                          {"name": "field2", "status": "locked"},
                          {"name": "field3", "status": "hidden"}]}
        params = {"form_id": "111", "field2": "value2", "field4": "value4"}
        with self.settings(FORM_CONFIGS=config):
            response = views.generate_form(None, "AGE", "APP", params)
            self.assertContains(response, "agency_id")
            self.assertContains(response, "AGE")
            self.assertContains(response, "app_name")
            self.assertContains(response, "APP")
            self.assertContains(response, "field1")
            self.assertContains(response, "field2")
            self.assertContains(response, "field3")
            self.assertContains(response, "value2")
            self.assertNotContains(response, "field4")
            self.assertNotContains(response, "value4")

    @patch('mockpay.views.send_status_to_agency')
    def test_exit_redirect(self, send_status_to_agency):
        """Test first a successful redirect, then a canceled redirect, then an
        error redirect (bad info from the agency server"""
        send_status_to_agency.return_value = {'response_message': 'OK'}
        data = {'failure_return_url': 'FFFF', 'success_return_url': 'SSSS',
                'agency_id': 'AGAGAG'}
        response = self.client.post(reverse('redirect'), data=data)
        self.assertNotContains(response, 'FFFF')
        self.assertContains(response, 'SSSS')

        data['cancel'] = 'Cancel'
        response = self.client.post(reverse('redirect'), data=data)
        self.assertContains(response, 'FFFF')
        self.assertNotContains(response, 'SSSS')

        del data['cancel']
        send_status_to_agency.return_value = "error occurred"
        response = self.client.post(reverse('redirect'), data=data)
        self.assertContains(response, 'FFFF')
        self.assertNotContains(response, 'SSSS')

        send_status_to_agency.return_value = {'response_message': 'Error'}
        response = self.client.post(reverse('redirect'), data=data)
        self.assertContains(response, 'FFFF')
        self.assertNotContains(response, 'SSSS')


class AccessSettingsTests(SimpleTestCase):
    def test_lookup_config(self):
        """Fetching a key should first look in the app info and cascade up"""
        mock_config = {"AGENCY": {"key_a": "value_1", "key_b": "value_2",
                                  "apps": {"APPNAME": {"key_b": "value_3"}}}}
        with self.settings(AGENCY_CONFIG=mock_config):
            #   Agency not present in config
            self.assertEqual(
                access_settings.lookup_config("key_b", "other", None), None)
            #   App not present in config
            self.assertEqual(
                access_settings.lookup_config("key_b", "AGENCY", "NONAPP"),
                None)
            #   Key not present in config
            self.assertEqual(
                access_settings.lookup_config("key_z", "AGENCY", "APPNAME"),
                None)
            #   App overrides Agency setting
            self.assertEqual(
                access_settings.lookup_config("key_b", "AGENCY", "APPNAME"),
                "value_3")
            #   Final parameter overrides everything
            self.assertEqual(
                access_settings.lookup_config("key_b", "AGENCY", "APPNAME",
                                              {"key_b": "value_10"}),
                "value_10")
            #   Falls back to Agency setting
            self.assertEqual(
                access_settings.lookup_config("key_a", "AGENCY", "APPNAME"),
                "value_1")
            self.assertEqual(
                access_settings.lookup_config("key_b", "AGENCY", None),
                "value_2")

    def test_clean_response(self):
        """Verify that required fields must be present, and that no additional
        fields are accepted"""
        nodata = access_settings.clean_response({})
        self.assertTrue(isinstance(nodata, str))

        data = {'protocol_version': 'pv', 'response_message': 'rm',
                'action': 'a', 'form_id': 'fi', 'agency_tracking_id': 'ati',
                'invalid_field': 'if'}
        new_field = access_settings.clean_response(data)
        self.assertTrue(isinstance(new_field, str))
        self.assertNotEqual(nodata, new_field)  # different errors

        del(data['invalid_field'])
        data['payment_amount'] = '20.25'
        result = access_settings.clean_response(data)
        self.assertEqual(data, result)
        self.assertNotEqual(id(data), id(result))
