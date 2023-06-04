import requests
import os
from dotenv import load_dotenv
import supabase
import datetime
from typing import Dict, Any
import json

load_dotenv()
PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN")
supabase_url = os.getenv("SUPABASE_URL")
supabase_api_key = os.getenv("SUPABASE_SERVICE_KEY")

client = supabase.Client(supabase_url, supabase_api_key)  # type: ignore

# 使用OAuth token设置headers
headers = {
    "Authorization": "Bearer " + str(PERSONAL_ACCESS_TOKEN),
    "Content-Type": "application/json",
}


def run_query(query: str, variables: Dict[str, Any]):
    request = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            f"Query failed with status code {request.status_code}. {request.json()}"
        )


def fetch_issues(label: str, after: str = None):
    # GraphQL query to fetch issues
    query = """
    query($label: String!, $after: String) {
        search(query: $label, type: ISSUE, first: 100, after: $after) {
            pageInfo {
                endCursor
                hasNextPage
            }
            nodes {
                ... on Issue {
                    url
                    title
                    state
                    createdAt
                    updatedAt
                    comments {
                        totalCount
                    }
                    labels(first: 10) {
                        nodes {
                            name
                        }
                    }
                    assignees(first: 10) {
                        nodes {
                            login
                        }
                    }
                    repository {
                        url
                        stargazers {
                            totalCount
                        }
                        primaryLanguage {
                            name
                        }
                    }
                }
            }
        }
    }
    """
    variables = {"label": f"is:issue label:{label}", "after": after}
    return run_query(query, variables)


def main():
    existing_issues = client.table("issues").select("url, state").execute()
    three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)

    labels = [
        "good-first-issue",
        "first-timers-only",
        "easy",
    ]

    for label in labels:
        end_cursor = None
        while True:
            result = fetch_issues(label, end_cursor)
            issues = result["data"]["search"]["nodes"]
            for issue in issues:
                created_at = datetime.datetime.strptime(
                    issue["createdAt"], "%Y-%m-%dT%H:%M:%SZ"
                )
                # Check if the issue is created within the last 3 months
                if created_at < three_months_ago:
                    break
                url = issue["url"]
                stars = issue["repository"]["stargazers"]["totalCount"]
                assignees = len(issue["assignees"]["nodes"])
                # Check if the issue satisfies the condition and does not exist in supabase
                if (
                    (assignees == 0 and stars >= 50)
                    or (assignees > 0 and stars >= 5000)
                ) and issue["state"] == "OPEN":
                    print(f"New good-first-issue found: {url}")
                    new_issue = {
                        "url": url,
                        "state": issue["state"],
                        "title": issue["title"],
                        "repository_owner": issue["repository"]["url"].split("/")[-2],
                        "repository": issue["repository"]["url"].split("/")[-1],
                        "created_at": issue["createdAt"],
                        "updated_at": issue["updatedAt"],
                        "comments": issue["comments"]["totalCount"],
                        "labels": ",".join(
                            label["name"] for label in issue["labels"]["nodes"]
                        ),
                        "stars": stars,
                        "primary_language": issue["repository"]["primaryLanguage"][
                            "name"
                        ]
                        if issue["repository"]["primaryLanguage"]
                        else None,
                        "assignees": ",".join(
                            assignee["login"]
                            for assignee in issue["assignees"]["nodes"]
                        ),
                    }
                    # Insert or update the issue
                    response = (
                        client.table("issues")
                        .upsert(new_issue, on_conflict="url")
                        .execute()
                    )
            # Check if there are more pages and if the issues are within the last 3 months
            if (
                result["data"]["search"]["pageInfo"]["hasNextPage"]
                and created_at >= three_months_ago
            ):
                end_cursor = result["data"]["search"]["pageInfo"]["endCursor"]
            else:
                break


if __name__ == "__main__":
    main()
