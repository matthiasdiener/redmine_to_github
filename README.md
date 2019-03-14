# redmine_to_github
Migrate Redmine issues to GitHub issues.

## Usage

1. Open `config.py` and change the variables pointing to your repositories, projects, user names, etc.
2. Run `./download_redmine.py` to download all issues of the project configured in the first step.
3. Run `./upload_github.py` to upload your issues to GitHub.
