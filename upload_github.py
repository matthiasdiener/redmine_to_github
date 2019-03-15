#!/usr/bin/env python3


import json
import os
import requests
import sys
import time

from config import *


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

    url = 'https://api.github.com/repos/{0}/milestones'.format(GITHUB_REPO)
    headers = {
    "Authorization": "token {0}".format(github_tokenmap[user])
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

    url = 'https://api.github.com/repos/{0}/milestones'.format(GITHUB_REPO)

    headers = {
    "Authorization": "token {0}".format(github_tokenmap[user])
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
        body = "No body."

    if realuser not in github_tokenmap:
        realuser = github_default_username
        body = "*Original author: " + user + "*\n\n---\n" + body

    if assignee not in github_tokenmap:
        assignee = github_default_username

    headers = {
    "Authorization": "token {0}".format(github_tokenmap[realuser])
    "Accept": "application/vnd.github.golden-comet-preview+json"
    }

    url = 'https://api.github.com/repos/{0}/import/issues'.format(GITHUB_REPO)

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

    # GitHub has a limit of 300 requests/per hour
    time.sleep(2)
    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code != 202:
        print('Could not create issue "{0}"'.format(title))
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

    orig_body = body
    body = "*Original date: " + ctime + "*\n\n---\n" + body

    realuser = user

    if realuser not in github_tokenmap:
        realuser = github_default_username
        body = "*Original author: " + user + "*\n" + body

    headers = {
        "Authorization": "token {0}".format(github_tokenmap[realuser])
    }


    url = 'https://api.github.com/repos/{0}/issues/{1}/comments'.format(GITHUB_REPO, issuenr)

    data = {'body' : body}

    payload = json.dumps(data)

    time.sleep(2)
    response = requests.request("POST", url, data=payload, headers=headers)

    if response.status_code != 201:
        print('Could not create comment: "{0}"'.format(body))
        print('Response:', response.content)
        sys.exit(1)
    else:
        if "X-RateLimit-Remaining" in response.headers: 
            print('  Created comment: {0} [...] ({1})'.format(orig_body.split('\n')[0], response.headers["X-RateLimit-Remaining"]))
        else:
            print('  Created comment: {0} [...] ({1})'.format(orig_body.split('\n')[0]), "unknown")



def get_github_username(redmine_user):
    if redmine_user in github_usermap:
        return(github_usermap[redmine_user])
    else:
        # print('  Redmine user "{0}" not in github_usermap, using default github author "{1}".'.format(redmine_user, github_default_username))
        return(github_default_username)



def create_issue_from_redmine_file(filename):

    with open(filename) as infile:
        indata = json.load(infile)

    redmine_user = indata["author"]["name"]

    github_author = get_github_username(redmine_user)

    filename_issue_num = int(os.path.basename(filename).split('.')[0])


    title = indata["subject"]
    body = translate_for_github(indata["description"])
    created_at = indata["created_on"]
    updated_at = indata["updated_on"]

    if "assigned_to" in indata:
        assignee = get_github_username(indata["assigned_to"]["name"])
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
    github_issue_num = make_issue(github_author, title, body, created_at, closed_at, updated_at, assignee, milestone, closed, labels)

    if github_issue_num != filename_issue_num:
        print('  Warning: GitHub issue number ({0}) does not match Redmine issue number ({1})!'.format(github_issue_num, filename_issue_num))

    # Add comments
    for j in indata["journals"]:
        github_author = get_github_username(j["user"]["name"])

        body = None

        if "notes" in j:
            body = translate_for_github(j["notes"])
        created_at = j["created_on"]

        created_at = created_at.replace("T", " ")
        created_at = created_at.replace("Z", "")

        if body == "" or body == None: continue

        make_comment(github_author, github_issue_num, body, created_at)


for f in sys.argv[1:]:
    create_issue_from_redmine_file(f)
