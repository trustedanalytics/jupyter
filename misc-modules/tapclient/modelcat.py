# vim: set encoding=utf-8

#  Copyright (c) 2016 Intel Corporation 
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
TAP Model Catalog Python Client
"""

__all__ = ["ModelCatalog"]

import logging
import requests
import httplib
from atable import dictionaries_to_atable


logger = logging.getLogger("tapclient")
logging.basicConfig(level=logging.INFO, handlers=logger)


listing_keys = ['id',
                'name',
                'revision',
                'algorithm',
                'description',
                'creationTool',
                'artifacts',
                'addedBy',
                'addedOn',
                'modifiedBy',
                'modifiedOn']


class ModelCatalogListings(object):
    """Holds response of a query of Model Catalog listings, with pretty-print string and json results"""

    def __init__(self, mc_response):
        self.response = mc_response

    def json(self):
        """JSON formatted objects of the listing data returned from the Model Catalog"""
        return self.response.json()

    def __repr__(self):
        return repr(dictionaries_to_atable(self.response.json(), keys=listing_keys))


def _get_security_token():
    """Gets the token required to speak with the TAP services"""
    with open('/tmp/.access_token', "r") as f:
        token = f.read()
        # os.getenv("TOKEN")

    token = token.strip()
    if not token.lower().startswith("bearer"):
        token = "bearer " + token

    return token


def _get_mc_host(host=None):
    """Gets the host of the ModelCatalog"""
    if host is None:
        return "model-catalog"  # this should resolve to IP address (and we assume port 80)


def _get_org():
    """Gets the org for this python session"""
    return '00000000-0000-0000-0000-000000000000'


class ModelCatalog(object):
    """Client object for communication with a ModelCatalog service instance"""

    def __init__(self, host=None, token_override=None):  # username=None, password=None):
        """
        Create client instance to talk to the Model Catalog

        :param host: (optional) the host:port of the Model Catalog to connect to
        :param token_override: (optional) if set, this value will always be used for the access token
        """
        self.host = _get_mc_host(host)
        self.token_override = token_override
        self.org = _get_org()

    def _get_token(self):
        return self.token_override or _get_security_token()

    def listings(self):
        """Returns the listings currently in the ModelCatalog (see ModelCatalogListings object)"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models?orgId=%s' % (self.host, self.org)
        response = requests.get(uri, headers=headers)
        if response.status_code == httplib.OK:
            return ModelCatalogListings(response)
        else:
            raise Exception("Could not fetch Org UUID for the user. Error: %s" % response.text)

    def get(self, listing_id):
        """Returns metadata for the given listing_id"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models/%s' % (self.host, listing_id)

        response = requests.get(uri, headers=headers)
        if response.status_code == httplib.OK:
            return response.json()
        else:
            raise Exception("Could not fetch model ID %s.  Error: %s" % (listing_id, response.text))

    def get_artifact(self, listing_id, artifact_id):
        """Returns metadata for the given artifcat"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models/%s/artifacts/%s' % (self.host, listing_id, artifact_id)

        response = requests.get(uri, headers=headers)
        if response.status_code == httplib.OK:
            return response.json()
        else:
            raise Exception("Could not fetch artifact %s for ID %s: %s" % (artifact_id, listing_id, response.text))

    def download_artifact(self, listing_id, artifact_id, dest_path):
        """Downloads the given artifact to the given path"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models/%s/artifacts/%s/file' % (self.host, listing_id, artifact_id)

        response = requests.get(uri, headers=headers)
        if response.status_code == httplib.OK:
            with open(dest_path, "w") as f:
                f.write(response.text)
            return response
        else:
            raise Exception("Could not download artifact %s for ID %s: %s" % (artifact_id, listing_id, response.text))

    def add(self,
            name,
            artifacts,
            revision=None,
            algorithm=None,
            creation_tool=None,
            description=None):
        """
        Add a listing to the model catalog

        :param name: (str) listing name
        :param artifacts: (list) a list of file paths of artifacts that should be uploaded for the listing
        :param revision: (str) Optional string to label the listing
        :param algorithm: (str) Optional name of the "algorithm" associated with this listing
        :param creation_tool: (str) Optional name of the tool or framework which created the listing's artifacts (for
                              example, "sparktk" or "Spark ML")
        :param description: (str) Optional description for the listing
        :return: the response object of the post request
        """

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        payload = {'name': name,
                   'revision': revision or '',
                   'algorithm': algorithm or '',
                   'creationTool': creation_tool or '<Unknown>',
                   'description': description or '',
                   'artifactsIds': []}

        uri = 'http://%s/api/v1/models?orgId=%s' % (self.host, self.org)
        response = requests.post(uri, headers=headers, json=payload)
        listing_id = response.json()['id']

        if artifacts:
            if not isinstance(artifacts, list):
                artifacts = [artifacts]
            for a in artifacts:
                self._add_artifact_with_curl(listing_id, a)

        response = self.get(listing_id)
        # print repr(dictionaries_to_atable([response], keys=listing_keys))
        return response

    def add_artifact(self, listing_id, artifact_path):
        """Add a single artifact to an existing listing"""
        return self._add_artifact_with_curl(listing_id, artifact_path)

    def _add_artifact(self, listing_id, artifact_path, **kwargs):
        # (experimental) todo: have not yet figured out how to make this add request properly using py requests module
        headers = {'Authorization': self._get_token(),  # 'Content-Type': 'multipart/form-data',
                   }

        data = {'artifactActions': "PUBLISH_TAP_SCORING_ENGINE",
                'artifactFile': (artifact_path, open(artifact_path, 'rb'))}  # , "application/octet-stream")}

        # files =  {'artifactFile': open(artifact_path, 'rb')}

        uri = 'http://%s/api/v1/models/%s/artifacts' % (self.host, listing_id)
        response = requests.post(uri, headers=headers, files=data)  # files=files)
        return response

    def _add_artifact_with_curl(self, listing_id, artifact_path):
        # backdoor method to add artifacts using curl, since we haven't figured out how to do it correctly with requests
        cmd_str = ' '.join(["""curl -v -X POST -H "Authorization: %s""""" % self._get_token(),
                            """-F 'artifactActions=["PUBLISH_TAP_SCORING_ENGINE"];type=application/json'""",
                            """-F "artifactFile=@%s;type=application/octet-stream""" % artifact_path,
                            """http://%s/api/v1/models/%s/artifacts""" % (self.host, listing_id)])
        from subprocess import call
        result = call(cmd_str, shell=True)
        return result

    def remove(self, listing_id):
        """Removes the listing from the Model Catalog"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models/%s' % (self.host, listing_id)
        response = requests.delete(uri, headers=headers)
        return response

    def remove_artifact(self, listing_id, artifact_id):
        """Removes an artifact from the listing"""
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self._get_token(),
                   }
        uri = 'http://%s/api/v1/models/%s/artifacts/%s' % (self.host, listing_id, artifact_id)
        response = requests.delete(uri, headers=headers)
        return response
