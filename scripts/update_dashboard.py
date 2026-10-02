import os
import re
import urllib.request
import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

USERNAME = "himanshu003-beep"

SVG_PATH = Path("assets/svg/id-dashboard.svg")

API_BASE = "https://api.github.com"

TOKEN = os.getenv("GITHUB_TOKEN")


# ============================================================
# GITHUB API
# ============================================================

def github_request(endpoint):
    url = f"{API_BASE}{endpoint}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-dashboard-updater",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(
        url,
        headers=headers
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


# ============================================================
# GET USER INFORMATION
# ============================================================

def get_user():
    return github_request(f"/users/{USERNAME}")


# ============================================================
# GET ALL PUBLIC REPOSITORIES
# ============================================================

def get_repositories():
    repositories = []

    page = 1

    while True:
        data = github_request(
            f"/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&sort=pushed"
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


# ============================================================
# CALCULATE DASHBOARD DATA
# ============================================================

def calculate_data(user, repositories):

    # Ignore forks and archived repositories
    active_repositories = [
        repo
        for repo in repositories
        if not repo.get("fork", False)
        and not repo.get("archived", False)
    ]

    repository_count = len(active_repositories)

    followers = user.get("followers", 0)

    total_stars = sum(
        repo.get("stargazers_count", 0)
        for repo in active_repositories
    )

    total_forks = sum(
        repo.get("forks_count", 0)
        for repo in active_repositories
    )

    # Most recently updated projects
    recent_projects = sorted(
        active_repositories,
        key=lambda repo: repo.get("pushed_at") or "",
        reverse=True
    )[:4]

    project_names = [
        repo.get("name", "Project")
        for repo in recent_projects
    ]

    while len(project_names) < 4:
        project_names.append("Coming Soon")

    return {
        "repositories": repository_count,
        "followers": followers,
        "stars": total_stars,
        "forks": total_forks,
        "projects": repository_count,
        "project_names": project_names[:4],
    }


# ============================================================
# SVG UPDATE HELPERS
# ============================================================

def update_marker(svg, marker, value):
    """
    Replace content between:

    <!-- MARKER_START -->
    ...
    <!-- MARKER_END -->
    """

    pattern = (
        rf"(<!-- {re.escape(marker)}_START -->)"
        rf".*?"
        rf"(<!-- {re.escape(marker)}_END -->)"
    )

    replacement = (
        rf"\1\n"
        rf"{value}\n"
        rf"\2"
    )

    new_svg, count = re.sub(
        pattern,
        replacement,
        svg,
        flags=re.DOTALL
    )

    if count == 0:
        print(f"WARNING: Marker not found: {marker}")
        return svg

    return new_svg


# ============================================================
# UPDATE SVG
# ============================================================

def update_svg(data):

    if not SVG_PATH.exists():
        raise FileNotFoundError(
            f"SVG file not found: {SVG_PATH}"
        )

    svg = SVG_PATH.read_text(
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Dashboard numbers
    # --------------------------------------------------------

    svg = update_marker(
        svg,
        "REPOSITORIES",
        str(data["repositories"])
    )

    svg = update_marker(
        svg,
        "FOLLOWERS",
        str(data["followers"])
    )

    svg = update_marker(
        svg,
        "STARS",
        str(data["stars"])
    )

    svg = update_marker(
        svg,
        "PROJECTS",
        str(data["projects"])
    )

    # --------------------------------------------------------
    # Project names
    # --------------------------------------------------------

    projects = data["project_names"]

    svg = update_marker(
        svg,
        "PROJECT_1",
        projects[0]
    )

    svg = update_marker(
        svg,
        "PROJECT_2",
        projects[1]
    )

    svg = update_marker(
        svg,
        "PROJECT_3",
        projects[2]
    )

    svg = update_marker(
        svg,
        "PROJECT_4",
        projects[3]
    )

    SVG_PATH.write_text(
        svg,
        encoding="utf-8"
    )

    print("Dashboard SVG updated successfully.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("======================================")
    print(" GitHub Dashboard Updater")
    print("======================================")

    print(f"GitHub User: {USERNAME}")
    print(f"SVG File: {SVG_PATH}")

    print("\nFetching GitHub profile...")

    user = get_user()

    print("Fetching repositories...")

    repositories = get_repositories()

    print(f"Repositories fetched: {len(repositories)}")

    data = calculate_data(
        user,
        repositories
    )

    print("\nDashboard Data")
    print("------------------------------")
    print(f"Repositories : {data['repositories']}")
    print(f"Followers    : {data['followers']}")
    print(f"Stars        : {data['stars']}")
    print(f"Forks        : {data['forks']}")
    print(f"Projects     : {data['projects']}")

    print("\nRecent Projects:")

    for index, project in enumerate(
        data["project_names"],
        start=1
    ):
        print(f"{index}. {project}")

    print("\nUpdating SVG...")

    update_svg(data)

    print("\n======================================")
    print(" Dashboard update completed!")
    print("======================================")


if __name__ == "__main__":
    main()