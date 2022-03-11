"""
Migrate Gitlab projects (or variables) 
between namespaces/groups/severs 
using Gitlab's official API, in Python3+

LOG readability (Info, Error, Debug):

- #### ---> Start of a function
- ## ---> LOG withing a function
"""

import argparse
import logging
import os
import sys

import gitlab
import project as init

__appname__ = os.path.splitext(os.path.basename(sys.argv[0]))[0]
LOG = logging.getLogger(__appname__)
BASIC_FORMAT = "[%(levelname)s]:[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
logging.basicConfig(format=BASIC_FORMAT)
LOG.setLevel(logging.DEBUG)


def parse_args():
    """
    Function to parse arguements from the CLI
    @return: list
    """
    parser = argparse.ArgumentParser(
        description="Minimal script to Migrate CI/CD variables from 1 project to another in Gitlab",
        usage="%(prog)s "
        "[-u GITLAB_SERVER_URL] "
        "[-mv] "
        "[-mp] "
        "[-p GITLAB_PATH_FOR_PROJECT_IMPORT] "
        "[-f LOCAL_PATH_FOR_PROJECT_IMPORT] "
        "[-s SOURCE_PROJECT_ID] "
        "[-d DESTINATION_PROJECT_ID] "
        "[-ba BOT_ACCESS_TOKEN] "
        "[-D]",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    #! Instantly print help & exit if no args were given
    if len(sys.argv) <= 1:
        parser.print_help()
        parser.exit()
    parser.add_argument(
        "-u",
        "--server_url",
        dest="server_url",
        action="store",
        default="",
        required=True,
        help="Gitlab Server URL",
    )
    parser.add_argument(
        "-mv",
        "--migrate_variables",
        dest="migrate_variables",
        action="store_true",
        default=False,
        required=False,
        help="Enables variable migration",
    )
    parser.add_argument(
        "-mp",
        "--migrate_project",
        dest="migrate_project",
        action="store_true",
        default=False,
        required=False,
        help="Enables full project migration",
    )
    parser.add_argument(
        "-p",
        "--path_import",
        dest="path_import",
        action="store",
        default="",
        required=False,
        help="Path or name of the project to be imported in Gitlab",
    )
    parser.add_argument(
        "-f",
        "--file_path_import",
        dest="file_path_import",
        action="store",
        default="",
        required=False,
        help="Local file of the project to be imported",
    )
    parser.add_argument(
        "-s",
        "--source_project_id",
        dest="source_project_id",
        action="store",
        default="0",
        required=True,
        help="Source project ID",
    )
    parser.add_argument(
        "-d",
        "--destination_project_id",
        dest="destination_project_id",
        action="store",
        default="0",
        required=True,
        help="Destination project ID",
    )
    parser.add_argument(
        "-ba",
        "--bot_access_token",
        dest="bot_access_token",
        action="store",
        default="",
        required=True,
        help="Access token for the bot that will be doing the API calls",
    )
    parser.add_argument(
        "-D",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        required=False,
        help="Output debugging messages",
    )
    return parser.parse_args()


def main():
    LOG.info("#### Reading Arguments ####")
    global args
    args = parse_args()
    LOG.info("#### Starting Migration Process ####")

    source_project = init.PROJECT(
        args.source_project_id, args.server_url, args.bot_access_token, args.debug
    )
    destination_project = init.PROJECT(
        args.destination_project_id, args.server_url, args.bot_access_token, args.debug
    )

    source_url, source_header = source_project.create_access_token("Tmp_Source_Token")
    destination_url, destination_header = destination_project.create_access_token(
        "Tmp_Destination_Token"
    )

    API = gitlab.API(
        args.server_url,
        source_project.project_id,
        destination_project.project_id,
        args.bot_access_token,
        args.debug,
    )

    if args.migrate_variables:
        LOG.info("#### 'Migrate Variables' (-mv) flag detected ####")
        source_variables = API.copy_source_variables(source_url, source_header)
        API.migrate_variables(source_variables, destination_url, destination_header)

    if args.migrate_project:
        if args.path_import is not None or args.file_path_import is not None:
            LOG.info("#### 'Migrate Project' (-mp) flag detected ####")
            API.export_project(source_project.project_id)
            API.import_project(args.path_import, args.file_path_import)
        else:
            LOG.ERROR("#### Both of the following arguments are required: -p/--path_import, -f/--file_path_import for a project migration ####")


if __name__ == "__main__":
    main()
