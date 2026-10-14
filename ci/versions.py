"""Select published stable Caddy releases and stable Cloudflare module tags."""

import json
import os
import re
import urllib.request


def stable_version(tag):
    match = re.fullmatch(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", tag)
    return tuple(map(int, match.groups())) if match else None


def latest_stable(items, releases=False):
    candidates = []
    for item in items:
        if releases and (item.get("draft") or item.get("prerelease")):
            continue
        tag = item.get("tag_name" if releases else "name", "")
        version = stable_version(tag)
        if version is not None:
            candidates.append(version)
    if not candidates:
        raise ValueError("No stable upstream version found")
    return ".".join(map(str, max(candidates)))


def github_items(repository, endpoint):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "homeserver-caddy-build",
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
    }
    result = []
    for page in range(1, 101):
        url = f"https://api.github.com/repos/{repository}/{endpoint}?per_page=100&page={page}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError("Unexpected GitHub API response")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise ValueError("GitHub pagination limit reached; refusing incomplete version selection")


def main():
    caddy = latest_stable(github_items("caddyserver/caddy", "releases"), releases=True)
    cloudflare = latest_stable(github_items("caddy-dns/cloudflare", "tags"))
    print(f"Selected Caddy {caddy}; Cloudflare module v{cloudflare}")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as output:
        output.write(f"CADDY_VERSION={caddy}\nCLOUDFLARE_VERSION=v{cloudflare}\n")


if __name__ == "__main__":
    main()
