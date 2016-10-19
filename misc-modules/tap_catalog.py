import getpass
import httplib
import json
import logging
import os
import random
import string
from itertools import imap

import requests
from tabulate import tabulate

INVALID_EXTENSION = "NA"
MAR_EXTENSION = "MAR"
MODEL_CATEGORY = "model"
ALL_CATEGORY = "all"
EXTENSION_DELIMITER = "."

tap_catalog_logger = logging.getLogger("tap_catalog")
logging.basicConfig(level=logging.INFO, handlers=tap_catalog_logger)


class _DataCatalogPublishJson(object):
    """
    Represents a data catalog publishable object
    """

    def __init__(self, target_uri, size=0, title=None, org_uuid=None, format=None, source_uri=None, is_public=False,
                 category=None, record_count=-1, data_sample=""):

        self.size = 0
        self.title = self._get_title_from_file(target_uri) if title is None else title
        self.orgUUID = org_uuid
        self.targetUri = target_uri
        self.format = self._get_format_from_extension(self.title) if format is None else format
        self.sourceUri = self.targetUri if source_uri is None else source_uri
        self.isPublic = is_public
        self.category = self._category_from_extension(self.format) if category is None else category
        self.recordCount = record_count
        self.dataSample = data_sample

    def _get_title_from_file(self, target_uri):
        tokens = os.path.split(target_uri)
        return tokens[-1]

    def _get_format_from_extension(self, file_name):
        delimiter = EXTENSION_DELIMITER
        if delimiter in file_name:
            return file_name.split(delimiter)[-1].upper()
        else:
            return INVALID_EXTENSION

    def _category_from_extension(self, format):
        if format == MAR_EXTENSION:
            return MODEL_CATEGORY
        else:
            return ALL_CATEGORY


class DataCatalog(object):
    """
    Create an instance of DataCatalog Client given TAP Domain URI and User credentials 
    Example:

    >>> from tap_catalog import DataCatalog
    >>> catalog = DataCatalog()
    >>> catalog.add("/user/vcap/count.csv")
    >>> catalog.add("hdfs://nameservice1/user/vcap/count.csv")
    
    """

    def __init__(self, uri=None, username=None, password=None):
        """
        Parameters:
        uri (str) : TAP Domain URI
        username (str) : TAP Username
        password (str) : TAP Password
        """
        if uri is None:
            self.uri = raw_input("Please input tap domain uri:")
        else:
            self.uri = uri
        if username is None:
            username = raw_input("Please input user name:")
        if password is None:
            password = getpass.getpass(prompt="Please input password:")
        self.client = "cf"
        self.client_password = ""
        self.data_catalog_uri = "data-catalog.%s" % self.uri
        self.uaa_uri = "uaa.%s" % self.uri
        self.api_uri = "api.%s" % self.uri
        self.scheme = "http://"
        tap_catalog_logger.info("Authenticating...")
        self.oauth = self._authenticate(username, password)
        tap_catalog_logger.info("Authenticated successfully.")

    def _generate_random_string(self, length):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

    def _authenticate(self, username, password):
        headers = {"Accept": "application/json"}
        uri = "%s%s/oauth/token" % (self.scheme, self.uaa_uri)
        payload = {"grant_type": "password", "scope": "", "username": username, "password": password}
        auth = (self.client, self.client_password)
        response = requests.post(uri, headers=headers, params=payload, auth=auth)
        if response.status_code == httplib.OK:
            return json.loads(response.text)
        else:
            raise Exception(
                "Could not authenticate. Please check the credentials which were used to initialize. Error: %s" % response.text)

    def _get_access_token(self):
        refresh_token = self.oauth["refresh_token"]
        headers = {"Accept": "application/json"}
        uri = "%s%s/oauth/token" % (self.scheme, self.uaa_uri)
        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        auth = (self.client, self.client_password)
        response = requests.post(uri, headers=headers, params=payload, auth=auth)
        if response.status_code == httplib.OK:
            return json.loads(response.text)["access_token"]
        else:
            raise Exception(
                "Could not authenticate. Please check the credentials which were used to initialize. Error: %s" % response.text)

    def _get_org_uuid(self):
        oauth_token = self._get_access_token()
        uri = "%s%s/v2/organizations" % (self.scheme, self.api_uri)
        headers = {"Authorization": "Bearer %s" % oauth_token, "Accept": "application/json"}
        response = requests.get(uri, headers=headers)
        if response.status_code == httplib.OK:
            resources = json.loads(response.text)["resources"]
            if len(resources) == 1:
                return resources[0]["metadata"]["guid"]
            else:
                tap_catalog_logger.info("User is enabled for multiple orgs. Please pick the Organization to publish")
                orgs = []
                for i in resources:
                    orgs.append(i["entity"]["name"])
                orgs_len = len(orgs)
                zipped = zip(range(1, orgs_len + 1), orgs)
                table = list(imap(lambda row: ["%s. %s" % (row[0], row[1])], zipped))
                tap_catalog_logger.info("\n" + tabulate(table))
                choice = int(raw_input("[1-%d]" % (orgs_len)))
                if choice not in range(1, orgs_len + 1):
                    raise Exception("Invalid choice")
                else:
                    return filter(lambda row: row["entity"]["name"] == orgs[choice - 1], resources)[0]["metadata"][
                        "guid"]
        else:
            raise Exception("Could not fetch Org UUID for the user. Error: %s" % response.text)

    def add(self, artifact_path):
        """
        Add an entry to data catalog
        Parameters:
        artifact_path (str) : Path to Artifact on HDFS (Accepts absolute Path on HDFS with or without Namenode information)
        """
        hdfs_scheme = "hdfs://nameservice1"  # Assumes HA on HDFS
        artifact_path = artifact_path if str.startswith(artifact_path, hdfs_scheme) else "%s%s" % (
        hdfs_scheme, artifact_path)

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers["Authorization"] = "Bearer %s" % self._get_access_token()
        rstring = self._generate_random_string(32)
        data_catalog_id = "%s-%s-%s-%s-%s" % (
        rstring[0:8], rstring[8:12], rstring[12:16], rstring[16:20], rstring[20:32])

        data_catalog_json = _DataCatalogPublishJson(target_uri=artifact_path, org_uuid=self._get_org_uuid())
        data = json.dumps(data_catalog_json.__dict__)
        data_catalog_uri = "%s%s/rest/datasets/%s" % (self.scheme, self.data_catalog_uri, data_catalog_id)
        response = requests.put(data_catalog_uri, headers=headers, data=data)
        if response.status_code == httplib.CREATED:
            tap_catalog_logger.info("Added file to Data Catalog successfully.")
        else:
            tap_catalog_logger.error("Failed to add file to Data Catalog. %s" % response.text)
