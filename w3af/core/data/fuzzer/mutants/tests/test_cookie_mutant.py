"""
test_cookie_mutant.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import unittest

from w3af.core.data.fuzzer.mutants.cookie_mutant import CookieMutant
from w3af.core.data.request.querystring_request import QsRequest
from w3af.core.data.request.post_data_request import PostDataRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.cookie import Cookie


class TestCookieMutant(unittest.TestCase):

    def setUp(self):
        self.fuzzer_config = {'fuzz_cookies': True}
        self.payloads = ['abc', 'def']
        self.url = URL('http://moth/')

    def test_basics(self):
        cookie = Cookie('foo=bar; spam=eggs')
        freq = QsRequest(self.url, cookie=cookie)

        m = CookieMutant(freq)
        m.set_var('foo', 0)
        m.set_token_value('abc')

        self.assertEqual(m.get_url().url_string, 'http://moth/')
        self.assertEqual(str(m.get_cookie()), 'foo=abc; spam=eggs;')

        expected_mod_value = 'The cookie data that was sent is: "foo=abc;'\
                             ' spam=eggs;".'
        generated_mod_value = m.print_token_value()

        self.assertEqual(generated_mod_value, expected_mod_value)

        expected_found_at = '"http://moth/", using HTTP method GET. The modified'\
                            ' parameter was the session cookie with value: '\
                            '"foo=abc; spam=eggs;".'
        generated_found_at = m.found_at()

        self.assertEqual(generated_found_at, expected_found_at)

    def test_config_false(self):
        fuzzer_config = {'fuzz_cookies': False}
        freq = QsRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = CookieMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_not_qs_request(self):
        fuzzer_config = {'fuzz_cookies': True}
        freq = PostDataRequest(URL('http://www.w3af.com/foo/bar'))

        generated_mutants = CookieMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_config_true(self):
        fuzzer_config = {'fuzz_cookies': True}

        cookie = Cookie('foo=bar; spam=eggs')
        freq = QsRequest(self.url, cookie=cookie)

        generated_mutants = CookieMutant.create_mutants(
            freq, self.payloads, [],
            False, fuzzer_config)

        self.assertNotEqual(len(generated_mutants), 0, generated_mutants)

    def test_no_cookie(self):
        freq = QsRequest(self.url)

        generated_mutants = CookieMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 0, generated_mutants)

    def test_valid_results(self):
        cookie = Cookie('foo=bar; spam=eggs')
        freq = QsRequest(self.url, cookie=cookie)

        generated_mutants = CookieMutant.create_mutants(
            freq, self.payloads, [],
            False, self.fuzzer_config)

        self.assertEqual(len(generated_mutants), 4, generated_mutants)

        expected_cookies = ['foo=abc; spam=eggs;',
                            'foo=def; spam=eggs;',
                            'foo=bar; spam=abc;',
                            'foo=bar; spam=def;'
                            ]

        generated_cookies = [str(m.get_cookie()) for m in generated_mutants]
        self.assertEqual(expected_cookies, generated_cookies)

        generated_cookies = [str(m.get_dc()) for m in generated_mutants]
        self.assertEqual(expected_cookies, generated_cookies)
