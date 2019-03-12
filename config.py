####################################################
# This file contains the user configuration.       #
# You will need to change the values in this file. #
####################################################

#
#   Redmine API information
#

# URL of the Redmine server
REDMINE_SERVER     = 'https://example.com/path/to/redmine/'

# Found in project URL: https://example.com/redmine/projects/PROJECT_ID
REDMINE_PROJECT_ID = 'project_id' 

# See http://www.redmine.org/projects/redmine/wiki/Rest_api#Authentication:
# You can find your API key on your account page.
REDMINE_API_KEY = 'redmine_api_key'

##########################################################

#
# GitHub API information
#

# The GitHub repository to add this issue to:
GITHUB_REPO_OWNER = 'github_repo_owner_name'
GITHUB_REPO_NAME  = 'github_repo_name'


# Maps Github user names to their Github access tokens:
github_tokenmap = {
    'github_username':                      'access token',
}


# Maps Redmine user names to Github user names:
github_usermap = {
    'redmine_username' :                    'github_username',
}
