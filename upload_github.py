#!/usr/bin/env python3


import json
import os
import requests
import sys
import time

from config import *


def translate_for_github(content):
    if not content:
        return None

    for hlvl in range(1, 7):
        content = content.replace('h{0}.'.format(hlvl), '#' * hlvl)

    content = content.replace('@', '`')        # inline code
    content = content.replace('\n# ', '1. ')   # lists
    content = content.replace('\r\n<pre>\r\n', '\n```\n')  # code block
    content = content.replace('<pre>', '\n```\n')  # code block
    content = content.replace('\r\n</pre>\r\n', '\n```\n') # code block
    content = content.replace('</pre>', '\n```\n') # code block

    if ('filter_redmine_bodytext_for_github' in dir(config)):
        content = filter_redmine_bodytext_for_github(content)
    
    return content


def make_request(_url, _user, _data=None, _type='GET', _headers={}):
    _headers['Authorization'] = 'token {0}'.format(get_github_token(_user))

    url = 'https://api.github.com/repos/{0}'.format(GITHUB_REPO) + _url

    time.sleep(2)
    response = requests.request(_type, url, data=_data, headers=_headers)

    return response

# Map from Redmine milestone name to Github milestone ID
milestones = {}

def get_milestones(user):
    if milestones:
        return 

    response = make_request('/milestones', user)

    j = json.loads(response.content)

    for n in j:
        milestones[n["title"]] = n["number"]


def create_milestone(user, title):

    get_milestones(user)

    if title == None:
        return None

    if title in milestones:
        return milestones[title]

    data = {"title": title}

    payload = json.dumps(data)

    response = make_request('/milestones', user, _data=payload, _type="POST")

    j = json.loads(response.content)

    milestones[title] = j["number"]

    return milestones[title]


def make_issue(user, title, body, created_at, closed_at, updated_at, assignee, milestone, closed, labels):
    # Create an issue on github.com using the given parameters

    realuser = get_github_username(user)

    if body == None:
        body = "No body."

    if not redmine_user_has_token(user):
        body = "*Original author: " + user + "*\n\n---\n" + body

    if assignee not in github_tokenmap:
        assignee = github_default_username

    headers = {
        "Accept": "application/vnd.github.golden-comet-preview+json"
    }

    url = 'https://api.github.com/repos/{0}/import/issues'.format(GITHUB_REPO)

    data = {'issue': {'title': title,
                      'body': body,
                      'created_at': created_at,
                      'updated_at': updated_at,
                      'assignee': assignee,
                      'milestone': create_milestone(github_default_username, milestone),
                      'closed': closed,
                      'labels': labels
                      }}
    if closed_at:
      data['issue']["closed_at"] = closed_at

    payload = json.dumps(data)

    response = make_request('/import/issues', realuser, _data=payload, _type="POST", _headers=headers)
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
                print('Issue #{0} "{1}" {2}'.format(num, title[:40], real_url))
                break

            if status == "failed":
                print(response.content)
                sys.exit(2)

        time.sleep(2)

    return num


def make_comment(user, issuenr, body, ctime):

    orig_body = body
    body = "*Original date: " + ctime + "*\n\n---\n" + body

    realuser = get_github_username(user)

    if not redmine_user_has_token(user):
        body = "*Original author: " + user + "*\n" + body


    url = '/issues/{0}/comments'.format(issuenr)

    data = {'body' : body}

    payload = json.dumps(data)

    response = make_request(url, realuser, _type="POST", _data=payload)

    if response.status_code != 201:
        print('Could not create comment: "{0}"'.format(body))
        print('Response:', response.content)
        sys.exit(1)
    else:
        if "X-RateLimit-Remaining" in response.headers: 
            print('  Comment: "{0}" ({1})'.format(orig_body.split('\n')[0][:50], response.headers["X-RateLimit-Remaining"]))
        else:
            print('  Comment: "{0}"'.format(orig_body.split('\n')[0][:50]))


def redmine_user_has_token(redmine_user):
    if redmine_user in github_usermap:
        github_user = github_usermap[redmine_user]
        if github_user in github_tokenmap:
            return True
    return False

unknown_github_username = set()
unknown_github_token = set()

def get_github_username(redmine_user):
    if redmine_user in github_usermap:
        return(github_usermap[redmine_user])
    else:
        if redmine_user not in unknown_github_username:
            print('  Redmine user "{0}" not in github_usermap, using default GitHub user "{1}".'.format(redmine_user, github_default_username))
            unknown_github_username.add(redmine_user)
        return(github_default_username)


def get_github_token(github_user):
    if github_user in github_tokenmap:
        return(github_tokenmap[github_user])
    else:
        if github_user not in unknown_github_token:
            print('  GitHub user "{0}" not in github_tokenmap, using token for default GitHub user "{1}".'.format(github_user, github_default_username))
            unknown_github_token.add(github_user)
        return(github_tokenmap[github_default_username])


def create_issue_from_redmine_file(filename):

    with open(filename) as infile:
        indata = json.load(infile)

    author = indata["author"]["name"]

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
    github_issue_num = make_issue(author, title, body, created_at, closed_at, updated_at, assignee, milestone, closed, labels)

    if github_issue_num != filename_issue_num:
        print('  ** Warning: GitHub issue number ({0}) does not match Redmine issue number ({1})! **'.format(github_issue_num, filename_issue_num))

    # Add comments
    for j in indata["journals"]:
        author = j["user"]["name"]

        body = None

        if "notes" in j:
            body = translate_for_github(j["notes"])
        created_at = j["created_on"]

        created_at = created_at.replace("T", " ")
        created_at = created_at.replace("Z", "")

        if body == "" or body == None: continue

        make_comment(author, github_issue_num, body, created_at)




files = sys.argv[1:]

print('='*80)
print('Uploading {0} issue(s) to GitHub repository "{1}".'.format(len(files), GITHUB_REPO))
print('='*80)


for f in files:
    create_issue_from_redmine_file(f)

print('='* 80)
print('Finished.')

if len(unknown_github_username) > 0:
    print('The following Redmine users did not have a GitHub username associated with them:')
    print(unknown_github_username)

if len(unknown_github_token) > 0:
    print('The following GitHub users did not have a GitHub token associated with them:')
    print(unknown_github_token)
