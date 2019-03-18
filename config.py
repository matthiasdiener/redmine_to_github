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

# Create dummy Redmine issues to keep Redmine and GitHub issue numbers synchronized? 
REDMINE_CREATE_DUMMY_ISSUE=True

##########################################################

#
# GitHub API information
#

# The GitHub repository to add this issue to:
GITHUB_REPO = 'owner/repository'

# Issues and comments will be assigned to this GitHub user if the real user is not
# in the map below
github_default_username = 'github_default_username'

# Maps Github user names to their Github access tokens. The tokens can be
# generated in Settings -> Developer Settings -> Personal access tokens,
# Generate new token. Only the public_repo scope is necessary.
github_tokenmap = {
    'github_username':                      'access token',
}

# Maps Redmine user names to Github user names:
github_usermap = {
    'redmine_username' :                    'github_username',
}
