![repo-size](https://img.shields.io/github/repo-size/vel-san/gitlab-migrator?label=Repo-Size&style=flat-square) [![contrib](https://img.shields.io/github/contributors/vel-san/gitlab-migrator?label=Contributors&style=flat-square)](https://github.com/Vel-San/gitlab-migrator/graphs/contributors) [![release](https://img.shields.io/github/v/release/vel-san/gitlab-migrator?label=Release&style=flat-square)](https://github.com/Vel-San/gitlab-migrator/releases)

# Gitlab Migrator

Migrate Gitlab projects (or variables) between namespaces/groups/severs using Gitlab's official API, in Python3+ // WIP

## Prerequisites

- Project ID for the `Source` repo (Usually found under the repo name in Gitlab)
- Project ID for the `Destination` repo (Usually found under the repo name in Gitlab)
- Bot Access token (Created under the Bot's Gitlab Account) for the API calls
  - Add this bot as a "Maintainer" in both, Source/Destination Projects

## Usage

### Locally

```bash
usage: migrate.py [-u GITLAB_SERVER_URL] [-mv] [-mp] [-p GITLAB_PATH_FOR_PROJECT_IMPORT] [-f LOCAL_PATH_FOR_PROJECT_IMPORT] [-s SOURCE_PROJECT_ID] [-d DESTINATION_PROJECT_ID] [-ba BOT_ACCESS_TOKEN] [-D]

Minimal script to Migrate CI/CD variables from 1 project to another in Gitlab

optional arguments:
  -h, --help            show this help message and exit
  -u SERVER_URL, --server_url SERVER_URL
                        Gitlab Server URL
  -mv, --migrate_variables
                        Enables variable migration
  -mp, --migrate_project
                        Enables full project migration
  -p PATH_IMPORT, --path_import PATH_IMPORT
                        Path or name of the project to be imported in Gitlab
  -f FILE_PATH_IMPORT, --file_path_import FILE_PATH_IMPORT
                        Local file of the project to be imported
  -s SOURCE_PROJECT_ID, --source_project_id SOURCE_PROJECT_ID
                        Source project ID
  -d DESTINATION_PROJECT_ID, --destination_project_id DESTINATION_PROJECT_ID
                        Destination project ID
  -ba BOT_ACCESS_TOKEN, --bot_access_token BOT_ACCESS_TOKEN
                        Access token for the bot that will be doing the API calls
  -D, --debug           Output debugging messages
```

## TO-DO

- (TBF)

### API Overriding (Dev Usage)

#### CURL

You can manually import an export using the following cURL command:

```bash
curl --request POST --header "PRIVATE-TOKEN: XXX" --form "path=your/project/name" --form "namespace=your/new/path" --form "override_params[squash_option]=always" --form "file=@XXX.tar.gz" "https://[GITLAB_SERVER_URL]/api/v4/projects/import"
```

where `override_params[XXX]=YYY` is a hash that you can use to override some settings in your export. Very useful when an Export doesn't usually give you all the project config! A full list of options to override can be found int he references link below.

## References

- [Project API](https://docs.gitlab.com/ee/api/projects.html#edit-project)
