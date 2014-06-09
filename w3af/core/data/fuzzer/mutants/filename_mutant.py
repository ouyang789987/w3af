"""
FileNameMutant.py

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
import urllib
import re

from w3af.core.data.fuzzer.mutants.urlparts_mutant import URLPartsMutant
from w3af.core.data.dc.nr_kv_container import NonRepeatKeyValueContainer
from w3af.core.data.request.querystring_request import QsRequest

CHUNK_RE = re.compile(r'([a-zA-Z0-9]+)')
CHUNK_RE_2 = re.compile(r'[a-zA-Z0-9]')


class FileNameMutant(URLPartsMutant):
    """
    This class is a filename mutant.
    """

    def __init__(self, freq):
        URLPartsMutant.__init__(self, freq)

    def get_mutant_type(self):
        return 'url filename'

    def get_url(self):
        """
        :return: The URL, as modified by "set_token_value()"
        """
        domain_path = self._freq.get_url().get_domain_path()

        # Please note that this double encoding is needed if we want to work
        # with mod_rewrite
        encoded = urllib.quote_plus(self._mutant_dc['modified_part'],
                                    self._safe_encode_chars)
        if self._double_encoding:
            encoded = urllib.quote_plus(encoded, safe=self._safe_encode_chars)

        domain_path.set_file_name(self._mutant_dc['start'] + encoded +
                                  self._mutant_dc['end'])
        return domain_path

    get_uri = get_url

    def get_data(self):
        return None

    def print_token_value(self):
        fmt = 'The sent %s is: "%s%s%s".'
        return fmt % (self.get_mutant_type(), self._mutant_dc['start'],
                      self._mutant_dc['modified_part'], self._mutant_dc['end'])

    def set_token_value(self, val):
        self._mutant_dc['modified_part'] = val

    def get_token_value(self):
        return self._mutant_dc['modified_part']

    def set_url(self, u):
        msg = 'You can\'t change the value of the URL in a FileNameMutant'\
              ' instance.'
        raise ValueError(msg)

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified parameter was the URL'\
              ' filename, with value: "%s".'
        return fmt % (self.get_url(), self.get_method(), self.get_token_value())

    @staticmethod
    def create_mutants(freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config, data_container=None):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        
        :param fuzzable_param_list: Please note that in this case the user
                                    specifies the chunk of the filename that
                                    he wants to fuzz. Chunks:
                                        foo.bar.html
                                        0   1   2
        """
        if not fuzzer_config['fuzz_url_filenames']:
            return []

        if not isinstance(freq, QsRequest):
            return []

        res = []
        fname = freq.get_url().get_file_name()
        fname_chunks = [x for x in CHUNK_RE.split(fname) if x]

        for idx, fn_chunk in enumerate(fname_chunks):

            if not (fuzzable_param_list == [] or idx in fuzzable_param_list):
                continue

            for mutant_str in mutant_str_list:

                if CHUNK_RE_2.match(fn_chunk):
                    divided_fname = NonRepeatKeyValueContainer()
                    divided_fname['start'] = ''.join(fname_chunks[:idx])
                    divided_fname['end'] = ''.join(fname_chunks[idx + 1:])
                    divided_fname['modified_part'] = \
                        (fn_chunk if append else '') + \
                        urllib.quote_plus(mutant_str)

                    freq_copy = freq.copy()
                    freq_copy.set_url(freq.get_url())

                    # Create the mutant
                    m = FileNameMutant(freq_copy)
                    m.set_original_value(fn_chunk)
                    m.set_var('modified_part')
                    m.set_mutant_dc(divided_fname)
                    m.set_token_value(mutant_str)
                    # Special for filename fuzzing and some configurations
                    # of mod_rewrite
                    m.set_double_encoding(False)
                    res.append(m)

                    # The same but with a different type of encoding!
                    # (mod_rewrite)
                    m2 = m.copy()
                    m2.set_safe_encode_chars('/')

                    if m2.get_url() != m.get_url():
                        res.append(m2)
        return res
