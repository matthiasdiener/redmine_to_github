#!/usr/bin/env python3

import sys
import requests
import json
import time
import os

# The GitHub repository to add this issue to
REPO_OWNER = ""
REPO_NAME = ''


# Maps Github user names to their Github access tokens
tokenmap = {
  "pplimport" :      "",
}


# Maps Redmine user names to Github user names
usermap = {
  "pplimport" :       "pplimport",
}

def get_translate_dict():
    d = {}
    for hlevel in range(1, 7):
        d['h%s.' % hlevel] = '#' * hlevel        # e.g. d['h2.'] = '##'
    d['\n# '] = '\n1. '  # lists
    d['<pre>'] = '```'  # code block
    d['</pre>'] = '\n```'  # code block
    d['@'] = '`'  # inline code
    return d

def translate_for_github(content):
    if not content:
        return None
    
    for k, v in get_translate_dict().items():
        content = content.replace(k, v)

    return content

# Map from milestone name to Github milestone ID
milestones = {}

def get_milestones(user):
    if milestones:
        return 

    url = 'https://api.github.com/repos/%s/%s/milestones' % (REPO_OWNER, REPO_NAME)
    headers = {
    "Authorization": "token %s" % tokenmap[user]
    }

    response = requests.request("GET", url, headers=headers)

    j = json.loads(response.content)

    for n in j:
        milestones[n["title"]] = n["number"]

def create_milestone(user, title):

    get_milestones(user)

    if title == None:
        return None

    if title in milestones:
        return milestones[title]

    url = 'https://api.github.com/repos/%s/%s/milestones' % (REPO_OWNER, REPO_NAME)

    headers = {
    "Authorization": "token %s" % tokenmap[user]
    }

    data = {"title": title}

    payload = json.dumps(data)

    time.sleep(2)
    response = requests.request("POST", url, data=payload, headers=headers)

    j = json.loads(response.content)

    milestones[title] = j["number"]

    return milestones[title]



def make_issue(user, title, body, created_at, closed_at, updated_at, assignee, milestone, closed, labels):
    # Create an issue on github.com using the given parameters

    realuser = user

    if body == None:
        body = ""

    if realuser not in tokenmap:
        realuser = "pplimport"
        body = "*Original author: " + user + "*\n\n---\n" + body

    if assignee not in tokenmap:
        assignee = "pplimport"

    headers = {
    "Authorization": "token %s" % tokenmap[realuser],
    "Accept": "application/vnd.github.golden-comet-preview+json"
    }

    url = 'https://api.github.com/repos/%s/%s/import/issues' % (REPO_OWNER, REPO_NAME)

    data = {'issue': {'title': title,
                      'body': body,
                      'created_at': created_at,
                      'updated_at': updated_at,
                      'assignee': assignee,
                      'milestone': create_milestone(realuser, milestone),
                      'closed': closed,
                      'labels': labels
                      }}
    if closed_at:
      data['issue']["closed_at"] = closed_at

    payload = json.dumps(data)

    # Add the issue to the repository
    time.sleep(1)
    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code != 202:
        print('Could not create issue "%s"' % title)
        print('Response:', response.content)
        sys.exit(1)

    status_url = json.loads(response.content)["url"]

    while True:
        response = requests.request("GET", status_url, headers=headers)
        r = json.loads(response.content)
        if "status" in r:
            status = r["status"]
            if status == "imported":
                issue_url = r["issue_url"]
                num = int(issue_url[issue_url.rfind("/")+1:])
                real_url = issue_url.replace("api.github.com/repos/", "github.com/")
                print ('Created issue #%d "%s" %s' % (num, title, real_url))
                break

            if status == "failed":
                print(response.content)
                sys.exit(2)

        time.sleep(2)

    return num


def make_comment(user, issuenr, body, ctime):

    body = "*Original date: " + ctime + "*\n\n---\n" + body

    realuser = user

    if realuser not in tokenmap:
        realuser = "pplimport"
        body = "*Original author: " + user + "*\n" + body

    headers = {
    "Authorization": "token %s" % tokenmap[realuser]
    }


    url = 'https://api.github.com/repos/%s/%s/issues/%s/comments' % (REPO_OWNER, REPO_NAME, issuenr)

    data = {'body' : body}

    payload = json.dumps(data)

    time.sleep(2)
    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.headers["X-RateLimit-Remaining"])

    if response.status_code != 201:
        print('Could not create comment: "%s"' % body)
        print('Response:', response.content)
        sys.exit(1)



def create_issue_from_redmine_file(filename):

    with open(filename) as infile:
        indata = json.load(infile)

    author = usermap[indata["author"]["name"]]

    title = indata["subject"]
    body = translate_for_github(indata["description"])
    created_at = indata["created_on"]
    updated_at = indata["updated_on"]

    if "assigned_to" in indata:
        assignee = usermap[indata["assigned_to"]["name"]]
    else:
        assignee = None

    if "fixed_version" in indata:
        milestone = indata["fixed_version"]["name"]
    else:
        milestone = None

    status = indata["status"]["name"]

    if status in ["Closed", "Invalid", "Merged", "Rejected"]:
        closed = True

        if "closed_on" in indata:
            closed_at = indata["closed_on"]
        else:
            closed_at = updated_at
    else:
        closed = False
        closed_at = None

    labels = [indata["tracker"]["name"].lower()]


    # Create issue
    num_issue = make_issue(author, title, body, created_at, closed_at, updated_at, assignee, milestone, closed, labels)

    # num_issue = int(os.path.basename(filename)[:-5])
    print(num_issue)
    # sys.exit(0)

    # Add comments
    for j in indata["journals"]:
        author = usermap[j["user"]["name"]]

        body = None

        if "notes" in j:
            body = translate_for_github(j["notes"])
        created_at = j["created_on"]

        created_at = created_at.replace("T", " ")
        created_at = created_at.replace("Z", "")

        if body == "" or body == None: continue

        make_comment(author, num_issue, body, created_at)


for f in sys.argv[1:]:
    create_issue_from_redmine_file(f)
