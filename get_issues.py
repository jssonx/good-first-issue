import requests
import time
import os
from dotenv import load_dotenv
import supabase
import datetime

load_dotenv()
PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN")
supabase_url = os.getenv("SUPABASE_URL")
supabase_api_key = os.getenv("SUPABASE_SERVICE_KEY")

# 使用OAuth token设置headers
headers = {"Authorization": "Token " + str(PERSONAL_ACCESS_TOKEN)}
client = supabase.Client(supabase_url, supabase_api_key)  # type: ignore


def fetch_repository_details(repository_owner, repository):
    url = f"https://api.github.com/repos/{repository_owner}/{repository}"
    response = requests.get(url, headers=headers)
    return response.json()


def fetch_issues(label):
    now = datetime.datetime.now()
    one_year_ago = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    url = f"https://api.github.com/search/issues?q=label:{label}+state:open+created:>{one_year_ago}&sort=created&order=desc"
    response = requests.get(url, headers=headers)
    return response.json()


def main():
    existing_issues = client.table("issues").select("url, state").execute()
    seen_issues = {issue["url"]: issue["state"] for issue in existing_issues.data}

    labels = ["help-wanted", "good-first-issue", "up-for-grabs", "first-timers-only"]
    issues = {}
    for label in labels:
        issues.update(
            {issue["html_url"]: issue for issue in fetch_issues(label)["items"]}
        )

    for url, issue in issues.items():
        state = issue["state"]
        title = issue["title"]
        repository_owner = issue["repository_url"].split("/")[-2]
        repository = issue["repository_url"].split("/")[-1]
        created_at = issue["created_at"]
        updated_at = issue["updated_at"]
        comments = issue["comments"]
        labels = [label["name"] for label in issue["labels"]]

        # 提取受托人信息
        assignees = issue["assignees"]
        assignee_names = [assignee["login"] for assignee in assignees]

        repository_details = fetch_repository_details(repository_owner, repository)
        stars = repository_details["stargazers_count"]
        primary_language = repository_details["language"]

        # 检查受托人条件和 star 数量条件
        if len(assignees) == 0 and stars >= 50 or len(assignees) > 0 and stars >= 5000:
            if url not in seen_issues:
                print(f"New good-first-issue found: {url}")
                seen_issues[url] = state

                new_issue = {
                    "url": url,
                    "state": state,
                    "title": title,
                    "repository_owner": repository_owner,
                    "repository": repository,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "comments": comments,
                    "labels": ",".join(labels),
                    "stars": stars,
                    "primary_language": primary_language,
                    "assignees": ",".join(assignee_names),
                }
                response = client.table("issues").insert([new_issue]).execute()


if __name__ == "__main__":
    main()
