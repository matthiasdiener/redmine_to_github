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

project_id = data['issues'][0]['project']['id']


def create_dummy_issue(id):
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

    print('  Issue {0} not found in project. Creating dummy issue to keep Redmine and GitHub issue IDs synchronized.'.format(id))
    open('issues/{0}.json'.format(id), 'w').write(dummy_issue)



print('Downloading {0} issues (maximum issue ID: {1}).'.format(issue_count,max_id))

for i in range(1,max_id+1):
    issue_query_str = 'issues/{0}.json?include=journals'.format(i)
    url = urljoin(REDMINE_SERVER, issue_query_str)
    r = requests.get(url, auth=auth)

    try:
        data = r.json()
    except:
        create_dummy_issue(i)
        continue

    if data['issue']['project']['id'] == project_id:
        issue = data['issue']
        print(issue['id'], issue['subject'])
        open('issues/{0}.json'.format(issue['id']), 'w').write(json.dumps(issue))
    else:
        create_dummy_issue(i)

print('Finished downloading {0} issues.'.format(issue_count))
