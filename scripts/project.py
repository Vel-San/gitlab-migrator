"""
Python3 -- Class for a Project

LOG readability (Info, Error, Debug):

- #### ---> Start of a function
- ## ---> LOG withing a function
"""

import logging
import json
import os
import sys
from datetime import datetime, timedelta

import requests

__appname__ = os.path.splitext(os.path.basename(sys.argv[0]))[0]
LOG = logging.getLogger(__appname__)
BASIC_FORMAT = "[%(levelname)s]:[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=BASIC_FORMAT)
LOG.setLevel(logging.DEBUG)


class PROJECT:
    """Gitlab project as objects"""

    def __init__(
        self, project_id: dict, server_url: str, bot_access_token: str, debug: bool
    ) -> None:
        """Initiate API object"""
        self.project_id = project_id
        self.server_url = server_url
        self.bot_access_token = bot_access_token
        self.head_token = {"PRIVATE-TOKEN": f"{bot_access_token}"}
        self.debug = debug

    def create_access_token(self, token_name: str):
        """
        Function to create Access Token w/ API for a project along with the URL/Header
        @return: {str} tuple
        """
        data = {
            "name": token_name,
            "scopes": ["api"],
            "expires_at": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        }
        LOG.info("#### Constructing project URL/Path ####")
        url_variables = f"https://{self.server_url}/api/v4/projects/{self.project_id}/variables?per_page=50"
        url_token = (
            f"https://{self.server_url}/api/v4/projects/{self.project_id}/access_tokens"
        )
        self.head_token["Content-Type"] = "application/json"
        tokens_ids_list = self.get_tokens_list(url_token, token_name)
        self.revoke_tokens(
            tokens_ids_list, url_token, token_name
        ) if tokens_ids_list else None
        LOG.debug(f"## Headers data {self.head_token} ##") if self.debug else None
        LOG.info(f"## Creating Access Token: ({token_name}) ##")
        LOG.debug(
            f"## Details for {token_name}: {json.dumps(data)} ##"
        ) if self.debug else None
        self.verify(url_token, self.head_token)
        self.head_token["Content-Type"] = "application/json"
        request = requests.post(
            url_token, headers=self.head_token, data=json.dumps(data)
        )
        parsed_request = json.dumps(request.json(), indent=4, sort_keys=True)
        json_obj = json.loads(parsed_request)
        LOG.info(f"## Access Token: ({json_obj['token']}) ##")
        header_variable = {"PRIVATE-TOKEN": f"{json_obj['token']}"}
        LOG.debug(
            f"Response output for {token_name}: {parsed_request}"
        ) if self.debug else None

        return url_variables, header_variable

    def verify(self, url: str, headers: str):
        """
        Function to verify URL/Paths of the project
        @return: {str} tuple
        """
        LOG.info("#### Verifying URL/Path ####")
        del headers["Content-Type"]
        request = requests.get(url, headers=headers)

        if request.status_code != 200:
            LOG.error(
                f"## Unable to connect to the project repository. Code: {request.status_code} | Reason: {request.reason} | Text: {request.text} ##"
            )
            sys.exit(1)

    def get_tokens_list(self, url: str, token_name: str):
        """
        Function to retrieve a list of all project Access Tokens
        @return: list
        """
        LOG.info(f"#### Checking for any old {token_name} Tokens ####")
        token_id_list = []
        tokens_request = requests.get(url, headers=self.head_token)
        for value in tokens_request.json():
            if token_name == value["name"]:
                token_id_list.append(value["id"])
        LOG.info(
            f"## Detected a total of {len(token_id_list)} '{token_name}' tokens ##"
        ) if len(token_id_list) != 0 else None
        LOG.debug(f"## Token IDs: {token_id_list} ##") if len(
            token_id_list
        ) != 0 and self.debug else None
        return (
            token_id_list
            if len(token_id_list) != 0
            else LOG.info(f"## No previous '{token_name}' detected! ##")
        )

    def revoke_tokens(self, token_ids: list, url: str, token_name: str):
        """
        Function used to check if there is already a `Tmp_Source_Token` and a `Tmp_Destination_Token`
        and revokes them, just to avoid having duplicate tokens
        """
        LOG.info(f"#### Attempting to revoke redundant '{token_name}' tokens ##")
        for token_id in token_ids:
            requests.delete(url=url + f"/{token_id}", headers=self.head_token)
            LOG.debug(
                f"## Token of ID '{token_id}' has been revoked ##"
            ) if self.debug else None
        LOG.info(f"## All previous '{token_name}' tokens have been revoked ##")
