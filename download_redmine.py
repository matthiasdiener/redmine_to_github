#!/usr/bin/env python3


from config import *
from urllib.parse import urljoin
import json
import requests


issue_query_str = 'issues.json?project_id={0}&limit=1&status_id=*'.format(REDMINE_PROJECT_ID)

url = urljoin(REDMINE_SERVER, issue_query_str)

auth = (REDMINE_API_KEY, 'random-pw')
r = requests.get(url, auth=auth)

data = r.json()

issue_count = data['total_count']
max_id = data['issues'][0]['id']

dummy_issue = '''
{
    "status": {
        "id": 1,
        "name": "Closed"
    },
    "project": {
        "id": 1,
        "name": "Charm++"
    },
    "attachments": null,
    "time_entries": null,
    "spent_hours": 0.0,
    "journals": [],
    "children": null,
    "description": ".",
    "subject": "Dummy issue",
    "changesets": null,
    "watchers": [],
    "author": {
        "id": 60,
        "name": "pplimport"
    },
    "created_on": "2010-05-23T19:25:24Z",
    "relations": null,
    "id": 77,
    "priority": {
        "id": 2,
        "name": "Normal"
    },
    "tracker": {
        "id": 4,
        "name": "Cleanup"
    },
    "updated_on": "2010-05-23T19:25:24Z",
    "total_spent_hours": 0.0,
    "start_date": "2010-05-23",
    "closed_on": "2010-05-23T19:25:24Z",
    "done_ratio": 0
}
'''


print('Downloading {0} issues (maximum issue ID: {1}).'.format(issue_count,max_id))

for i in range(1,max_id+1):
    issue_query_str = 'issues.json?project_id={0}&status_id=*&issue_id={1}'.format(REDMINE_PROJECT_ID, i)
    url = urljoin(REDMINE_SERVER, issue_query_str)
    r = requests.get(url, auth=auth)
    data = r.json()

    if len(data['issues'])>0:
        issue = data['issues'][0]
        print(issue['id'], issue['subject'])

        open('issues/{0}.json'.format(issue['id']), 'w').write(json.dumps(issue))
    else:
        print('    Issue {0} not found. Creating dummy issue to keep Redmine and GitHub issue IDs synchronized.'.format(i))
        open('issues/{0}.json'.format(i), 'w').write(dummy_issue)
