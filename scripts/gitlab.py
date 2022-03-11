"""
Python3 -- Class for Gitlab API

LOG readability (Info, Error, Debug):

- #### ---> Start of a function
- ## ---> LOG withing a function
"""

import json
import logging
import os
import sys
import time
import urllib

import requests

__appname__ = os.path.splitext(os.path.basename(sys.argv[0]))[0]
LOG = logging.getLogger(__appname__)
BASIC_FORMAT = "[%(levelname)s]:[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=BASIC_FORMAT)
LOG.setLevel(logging.DEBUG)


class API:
    """Gitlab API functions"""

    def __init__(
        self,
        server_url: str,
        source_project_id: dict,
        destination_project_id: dict,
        bot_access_token: str,
        debug: bool,
    ) -> None:
        """Initiate API object"""
        self.server_url = server_url
        self.source_project_id = source_project_id
        self.destination_project_id = destination_project_id
        self.head_token = {"PRIVATE-TOKEN": f"{bot_access_token}"}
        self.export_download_link = None
        self.debug = debug

    def copy_source_variables(self, source_url: str, source_headers: str):
        """
        Function to verify URL/Paths of the source & copy all variables
        @return: {json} list
        """
        LOG.info("#### Grabbing variables from Source ####")
        source_request = requests.get(source_url, headers=source_headers)
        parsed_request = json.dumps(source_request.json(), indent=4, sort_keys=True)

        LOG.debug(f"Json response from Source {parsed_request}") if self.debug else None
        LOG.info(f"## Total variables found: {len(source_request.json())} ##")
        if len(source_request.json()) == 0:
            LOG.error("## No variables found in source. Skipping migration process ##")
            sys.exit(1)
        return source_request.json()

    def paste_destination_variables(
        self,
        url: str,
        headers: dict,
        v_type: str,
        v_name: str,
        v_value: str,
        v_protected: bool,
        v_masked: bool,
        v_environment_scope: str,
    ):
        """
        Function to copy variables to the destination project
        """
        data = {
            "variable_type": v_type,
            "key": v_name,
            "value": v_value,
            "protected": v_protected,
            "masked": v_masked,
            "environment_scope": v_environment_scope,
        }
        LOG.info(f"## Pasting ({v_name}) ##")
        LOG.debug(f"## Details for {v_name}: {data} ##") if self.debug else None
        requests.post(url, headers=headers, data=data)

    def migrate_variables(
        self, source_vars: list, destination_url: str, destination_header: str
    ):
        """
        Function to Copy/Paste all variables from our source to the destination
        """
        for variable in source_vars:
            self.paste_destination_variables(
                destination_url,
                destination_header,
                variable["variable_type"],
                variable["key"],
                variable["value"],
                variable["protected"],
                variable["masked"],
                variable["environment_scope"],
            )

    def request_export(self, project_id: dict):
        """
        Function to export a project
        @return requests.models.Response
        """
        LOG.info(
            f"#### Requesting export from Gitlab API for project: {project_id} ####"
        )
        return requests.post(
            f"https://{self.server_url}/api/v4/projects/{project_id}/export",
            headers=self.head_token,
        )

    def request_export_status(self, project_id: dict):
        """
        Function to check the current status of an export
        @return requests.models.Response
        """
        LOG.info(f"#### Checking export status of project: {project_id} ####")
        return requests.get(
            f"https://{self.server_url}/api/v4/projects/{project_id}/export",
            headers=self.head_token,
        )

    def export_project(self, project_id: dict):
        """
        Function that handles both, exporting the project, checking the export status
        and generating download URLs for the files
        """
        LOG.info(f"#### Processing the export of project: {project_id} ####")
        export_request = self.request_export(project_id)
        if self.verify_api(export_request, "export"):
            export_status_str = ""
            export_status_success = ["finished"]
            export_status_pending = [
                "queued",
                "started",
                "finished",
                "regeneration_in_progress",
            ]
            export_status_unknown = ["unknown"]
            export_status_bool = False
            count = 0
            while not export_status_bool:
                LOG.info("## Waiting to complete exporting... ##")
                export_request = self.request_export_status(project_id)
                count += 1
                if count == 10:
                    LOG.error(
                        "## Project export is taking way too much time, something is wrong! ##"
                    )
                if self.verify_api(export_request, "export status request"):
                    json = export_request.json()
                    if "export_status" in json.keys():
                        export_status_str = json["export_status"]
                        if (
                            export_status_str in export_status_success
                            and "_links" in json.keys()
                        ):
                            LOG.info("## Export Complete! ##")
                            LOG.debug(
                                f"## JSON Output of the export: {json} ##"
                            ) if self.debug else None
                            export_status_bool = True
                            break
                        if export_status_str in export_status_pending:
                            LOG.info(
                                f"## ({count}) Export status: {export_status_str.upper()}... ##"
                            )
                            LOG.debug(
                                f"## JSON Output of the export: {json} ##"
                            ) if self.debug else None
                    else:
                        export_status_str = export_status_unknown[0]
                        LOG.info(
                            f"## ({count}) Export status: {export_status_str.upper()}... ##"
                        )

                time.sleep(5)

            if export_status_bool:
                if "_links" in json.keys():
                    self.export_download_link = json["_links"]
                    self.download_from_url(
                        self.export_download_link["api_url"],
                        "exported_projects",
                        project_id + ".tar.gz",
                    )
                else:
                    LOG.info(
                        f"## Unable to find download link in API response: {str(json)} ##"
                    )
            else:
                LOG.error(
                    f"## Export failed {export_request.reason} | Text: {export_request.text} ##"
                )

    def request_import(
        self, project_path: str, project_namespace: str, upload_from: str
    ):
        """
        Function to send a POST request for importing a previously exported project
        """
        LOG.info(
            f"#### Requesting import from Gitlab API for project: {project_path} ####"
        )
        import_data = {
            "path": project_path,
            "namespace": project_namespace,
            # "override_params[squash_option]": "always",
        }
        return requests.post(
            f"https://{self.server_url}/api/v4/projects/import",
            data=import_data,
            files={"file": ("Upload_Me.tar.gz", open(upload_from, "rb"))},
            headers=self.head_token,
        )

    def request_import_status(self, project_name: str, project_id: str):
        """
        Function to send a GET request and check for the status of an import
        """
        LOG.info(f"#### Checking import status of project: {project_name} ####")
        return requests.get(
            f"https://{self.server_url}/api/v4/projects/{project_id}/import",
            headers=self.head_token,
        )

    def import_project(
        self,
        project_path: str,
        upload_from: str,
    ):
        """
        Function that processes the import procedure
        """
        LOG.info(f"#### Processing the import of project: {project_path} ####")
        project_name = os.path.basename(project_path)
        project_namespace = os.path.dirname(project_path)
        local_file_path = os.path.join(os.getcwd(), upload_from)
        LOG.debug(
            f"## Import Name: {project_name} | Import Namespace: {project_namespace} | Importing from: {local_file_path}"
        )

        import_request = self.request_import(
            project_name, project_namespace, local_file_path
        )

        if self.verify_api(import_request, "import"):
            json = import_request.json()
            imported_project_id = json["id"]
            import_status_str = ""
            import_status_success = ["finished"]
            import_status_pending = [
                "scheduled",
                "started",
            ]
            import_status_failed = ["failed"]
            import_status_unknown = ["unknown", "none"]
            import_status_bool = False
            count = 0
            while not import_status_bool:
                LOG.info("## Waiting to complete importing... ##")
                import_request = self.request_import_status(
                    project_name, imported_project_id
                )
                count += 1
                if count == 10:
                    LOG.error(
                        "## Project import is taking way too much time, something is wrong! ##"
                    )
                if self.verify_api(import_request, "import status request"):
                    json = import_request.json()
                    if "import_status" in json.keys():
                        import_status_str = json["import_status"]
                        if import_status_str in import_status_success:
                            LOG.info("## Import Complete! ##")
                            LOG.debug(
                                f"## JSON Output of the import: {json} ##"
                            ) if self.debug else None
                            import_status_bool = True
                            break
                        if import_status_str in import_status_pending:
                            LOG.info(
                                f"## ({count}) Import status: {import_status_str.upper()}... ##"
                            )
                            LOG.debug(
                                f"## JSON Output of the import: {json} ##"
                            ) if self.debug else None
                        if import_status_str in import_status_failed:
                            LOG.error(f"## Import has failed! ##")
                            LOG.debug(
                                f"## JSON Output of the import: {json} ##"
                            ) if self.debug else None
                            exit(1)
                    else:
                        import_status_str = import_status_unknown[0]
                        LOG.info(
                            f"## ({count}) Import status: {import_status_str.upper()}... ##"
                        )
                        LOG.debug(
                            f"## JSON Output of the import: {json} ##"
                        ) if self.debug else None

                time.sleep(5)

    def verify_api(self, request: requests.models.Response, usage: str):
        """
        Function to check for Valid API status codes
        @return: boolean
        """
        if request.status_code >= 200 and request.status_code < 300:
            LOG.debug(
                f"#### '{request.url}' API Request is OK ####"
            ) if self.debug else None
            return True
        else:
            LOG.error(
                f"## '{request.url}' API is NOT OK -- Aborting the {usage}. Code: {request.status_code} | Reason: {request.reason} | Text: {request.text} ##"
            )
            sys.exit(1)

    def download_from_url(
        self, download_url: str, directory_name: str, project_id: dict
    ):
        """
        Function to simply download the exported project locally
        """
        LOG.info(
            f"#### Attempting to download the exported project locally | {download_url} ####"
        )
        download_Request = requests.get(
            download_url, allow_redirects=True, stream=True, headers=self.head_token
        )
        if self.verify_api(download_Request, "download"):
            if not os.path.exists(directory_name):
                os.makedirs(directory_name)
            file_path = os.path.join(directory_name, project_id)
            LOG.info(
                f"## Exported project is being saved under {os.path.abspath(file_path)} ##"
            )
            with open(file_path, "wb") as f:
                for chunk in download_Request.iter_content(chunk_size=1024 * 8):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())
