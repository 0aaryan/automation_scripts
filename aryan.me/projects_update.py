import base64
import json
import re
import os
import logging
from github import Github
import ruamel.yaml
from git import Repo


USERNAME = "0aaryan"
REPO_NAME = "0aaryan.github.io"
GH_PAT = os.environ.get('GH_PAT')




yaml = ruamel.yaml.YAML()

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_json_item(readme_content):
    try:
        json_data = re.findall(r"<!---([\s\S]*?)--->", readme_content)[0]
        return json.loads(json_data)
    except (IndexError, json.JSONDecodeError) as e:
        logging.error(f"Error extracting JSON data: {e}")
        print(f"Error extracting JSON data: {e}")
        return None

def get_readme_data(github_instance, username):
    try:
        user = github_instance.get_user(username)
        items = []
        for repo in user.get_repos():
            try:
                readme = repo.get_readme()
                if not readme:
                    continue
                readme_content = base64.b64decode(readme.content).decode('utf-8')
                json_item = get_json_item(readme_content)
                if json_item:
                    items.append(json_item)
            except Exception as e:
                logging.warning(f"Error processing repo {repo.name}: {e}")
                print(f"Error processing repo {repo.name}: {e}")
        return items
    except Exception as e:
        logging.error(f"Error fetching user {username}'s repositories: {e}")
        print(f"Error fetching user {username}'s repositories: {e}")
        return []

def save_data(data, output_dir):
    try:

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        project_json_path = os.path.join(output_dir, "projects.json")
        project_yaml_path = os.path.join(output_dir, "projects.yaml")

        with open(project_json_path, "w") as f:
            json.dump(data, f)

        with open(project_yaml_path, "w") as f:
            yaml.dump(data, f)
    except Exception as e:
        logging.error(f"Error saving data: {e}")
        print(f"Error saving data: {e}")

def update_hugo(hugo_file, projects_file):
    try:
        with open(projects_file) as f:
            projects = yaml.load(f)

        with open(hugo_file) as f:
            hugo = yaml.load(f)

        hugo["params"]["projects"] = projects["projects"]

        with open(hugo_file, "w") as f:
            yaml.dump(hugo, f)
    except Exception as e:
        logging.error(f"Error updating hugo file: {e}")
        print(f"Error updating hugo file: {e}")


def clone_github_repository(repo_name):
    try:
        repo_url = f"https://github.com/{repo_name}.git"
        target_directory = os.path.basename(repo_name)

        if os.path.exists(target_directory):
            repo = Repo(target_directory)
            origin = repo.remote('origin')
            origin.pull()
        else:
            repo = Repo.clone_from(repo_url, target_directory)

        return repo
    except Exception as e:
        logging.error(f"Error cloning repository {repo_name}: {e}")
        print(f"Error cloning repository {repo_name}: {e}")
        return None


def push_with_pat(repo, pat, commit_message):
    try:
        remote_url = repo.remote().url
        if "https://" in remote_url:
            remote_url_with_pat = remote_url.replace("https://", f"https://{pat}@")
        else:
            remote_url_with_pat = remote_url

        repo.remote().set_url(remote_url_with_pat)

        # Push the changes

        origin = repo.remote('origin')
        origin.push()
        print("Pushed to repo")
    except Exception as e:
        logging.error(f"Error pushing to repository: {e}")
        print(f"Error pushing to repository: {e}")



def main():
    try:

        g = Github(GH_PAT)

        print("Fetching data")
        project_json = {
            "projects": {
                "enable": True,
                "items": get_readme_data(g, USERNAME)
            }
        }

        save_data(project_json, "data")
        print("Data saved")
        print("clonning repo")
        repo = clone_github_repository(USERNAME + "/" + REPO_NAME)
        if repo:
            print("updating hugo ")
            update_hugo(REPO_NAME + "/hugo.yaml", "data/projects.yaml")
            print("pushing to repo")
            push_with_pat(repo, GH_PAT, "projects scrpit - Updated projects")
    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")



if __name__ == "__main__":
    if GH_PAT is None:
        print("Please set the GH_PAT environment variable")
    else:
        main()
