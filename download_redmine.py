#!/usr/bin/env python3

from config import *
from urllib.parse import urljoin
import json
import requests
import os
import sys

# all issues are stored in issues/
os.makedirs('issues', exist_ok=True)


# Get issue count and max. issue ID
issue_query_str = 'issues.json?project_id={0}&limit=1&status_id=*'.format(REDMINE_PROJECT_ID)

url = urljoin(REDMINE_SERVER, issue_query_str)

auth = (REDMINE_API_KEY, 'random-pw')
r = requests.get(url, auth=auth)

data = r.json()

issue_count = data['total_count']
max_id = data['issues'][0]['id']

pad_len = len(str(max_id))


# Get Project ID
url = urljoin(REDMINE_SERVER, 'projects.json')

r = requests.get(url, auth=auth)
data = r.json()

project_id = -1

for i in range(0,len(data['projects'])):
    if data['projects'][i]['identifier'] == REDMINE_PROJECT_ID:
        project_id = i

if project_id == -1:
    print("Error: Project {0} not found on {1}, exiting.".format(REDMINE_PROJECT_ID,REDMINE_SERVER))
    sys.exit(1)


def create_dummy_issue(i):
    dummy_issue = '''
    {{
        "status": {{
            "id": {0},
            "name": "Closed"
        }},
        "project": {{
            "id": 1,
            "name": "{1}"
        }},
        "attachments": null,
        "time_entries": null,
        "spent_hours": 0.0,
        "journals": [],
        "children": null,
        "description": ".",
        "subject": "Dummy issue",
        "changesets": null,
        "watchers": [],
        "author": {{
            "id": 60,
            "name": "{2}"
        }},
        "created_on": "2010-05-23T19:25:24Z",
        "relations": null,
        "id": 77,
        "priority": {{
            "id": 2,
            "name": "Normal"
        }},
        "tracker": {{
            "id": 4,
            "name": "Cleanup"
        }},
        "updated_on": "2010-05-23T19:25:24Z",
        "total_spent_hours": 0.0,
        "start_date": "2010-05-23",
        "closed_on": "2010-05-23T19:25:24Z",
        "done_ratio": 0
    }}
    '''.format(i, REDMINE_PROJECT_ID, github_default_username)

    open('issues/{0}.json'.format(str(i).zfill(pad_len)), 'w').write(dummy_issue)
    print('  Issue #{0} not found in project. Created dummy issue to keep Redmine and GitHub issue IDs synchronized.'.format(i))



print('Downloading {0} issues (maximum issue ID: {1}).'.format(issue_count,max_id))

for i in range(1,max_id+1):
    issue_query_str = 'issues/{0}.json?include=journals'.format(i)
    url = urljoin(REDMINE_SERVER, issue_query_str)
    r = requests.get(url, auth=auth)

    try:
        data = r.json()
    except:
        if REDMINE_CREATE_DUMMY_ISSUE:
            create_dummy_issue(i)
        continue

    if data['issue']['project']['id'] == project_id:
        issue = data['issue']
        open('issues/{0}.json'.format(str(issue['id']).zfill(pad_len)), 'w').write(json.dumps(issue))
        print('Issue #{0} "{1}" downloaded.'.format(issue['id'], issue['subject']))
    else:
        if REDMINE_CREATE_DUMMY_ISSUE:
            create_dummy_issue(i)

print('Finished downloading {0} issues.'.format(issue_count))
