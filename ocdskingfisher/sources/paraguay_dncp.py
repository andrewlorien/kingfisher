import csv
import hashlib
import json

import requests

from ocdskingfisher import util
from ocdskingfisher.base import Source
from ocdskingfisher.util import get_url_request

REQUEST_TOKEN = "Basic " \
                "ODhjYmYwOGEtMDcyMC00OGY1LWFhYWUtMWVkNzVkZmFiYzZiOjNjNjQxZGQ5LWNjN2UtNDI5ZC05NWRiLWI5ODNiNmYyMDY3NA== "


class ParaguayDNCPSource(Source):
    """
    API documentation: https://www.contrataciones.gov.py/datos/api/v2/
    Additional documentation: https://www.contrataciones.gov.py/datos/open-contracting-info
    """

    publisher_name = 'Paraguay DNCP'
    url = 'https://www.contrataciones.gov.py/datos'
    source_id = 'paraguay_dncp'

    def gather_all_download_urls(self):
        record_package_ids = []

        for year in range(2016, (2017 if self.sample else 2019)):
            record_package_ids += self.fetchRecordPackageIDs(year)

        if self.sample:
            record_package_ids = record_package_ids[:5]

        out = []

        for record_package_id in record_package_ids:
            out.append({
                'url': 'https://www.contrataciones.gov.py:443/datos/api/v2/doc/ocds/record-package/%s' % record_package_id,
                'filename': 'record-%s.json' % record_package_id,
                'data_type': 'record_package',
            })

        return out

    # @rate_limited(0.3)
    def fetchRecordPackageIDs(self, year):
        '''
        Download the CSV file for a particular year, and
        extract the list of record package IDs.
        '''
        url = 'https://www.contrataciones.gov.py/'
        url += 'images/opendata/planificaciones/%s.csv' % year
        r = util.get_url_request(url)
        if r[1]:
            raise Exception(r[1])
        r = r[0]
        decoded_content = r.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        id_list = []
        for row in cr:
            id_list.append(row[2])
        return id_list[1:]

    # @rate_limited(0.3)
    def save_url(self, filename, data, file_path):
        errors = self.save_content(data['url'], file_path, headers={"Authorization": self.getAccessToken()})
        return self.SaveUrlResult(errors=errors)

    def save_content(self, url, filepath, headers=None):
        request, errors = get_url_request(url, stream=True, headers=headers)
        if any('Request exception (Code %s)' % 401 in s for s in errors):
            self.access_token = None
            errors = self.save_content(url, filepath, headers={"Authorization": self.getAccessToken()})
        if not request:
            return errors

        try:
            with open(filepath, 'wb') as f:
                for chunk in request.iter_content(1024 ^ 2):
                    f.write(chunk)
            return []
        except Exception as e:
            return [str(e)]

    access_token = None

    def getAccessToken(self):
        if self.access_token:
            return "Bearer " + self.access_token
        else:
            correct = False
            json = ''
            while not correct:
                r = requests.post("https://www.contrataciones.gov.py:443/datos/api/oauth/token",
                                  headers={"Authorization": REQUEST_TOKEN})
                try:
                    json = r.json()['access_token']
                    correct = True
                except requests.exceptions.RequestException:
                    correct = False
            self.access_token = json
            return "Bearer " + json
