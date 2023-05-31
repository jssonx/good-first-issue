import requests
import time
import os
from dotenv import load_dotenv
import supabase

load_dotenv()
PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN")
supabase_url = os.getenv("SUPABASE_URL")
supabase_api_key = os.getenv("SUPABASE_SERVICE_KEY")

# 使用OAuth token设置headers
headers = {"Authorization": "Token " + str(PERSONAL_ACCESS_TOKEN)}
client = supabase.Client(supabase_url, supabase_api_key)  # type: ignore


def fetch_issues():
    url = "https://api.github.com/search/issues?q=label:good-first-issue+state:open&sort=created&order=desc"
    response = requests.get(url, headers=headers)
    return response.json()


def main():
    # 从Supabase中获取已经存在的issue URL
    existing_issues = client.table("issues").select("url").execute()
    seen_issues = {issue["url"] for issue in existing_issues.data}

    while True:
        issues = fetch_issues()

        for issue in issues["items"]:
            url = issue["html_url"]

            if url not in seen_issues:
                print(f"New good-first-issue found: {url}")
                seen_issues.add(url)

                # 将新发现的issue保存到Supabase
                response = client.table("issues").insert([{"url": url}]).execute()
                print(response)

        # 每5分钟检查一次
        time.sleep(5 * 60)


if __name__ == "__main__":
    main()
