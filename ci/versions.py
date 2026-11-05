"""Select published stable Caddy releases and stable Cloudflare module tags."""

import json
import os
import re
import urllib.error
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


def missing_caddy_base_images(version):
    token_url = "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/caddy:pull"
    with urllib.request.urlopen(token_url, timeout=30) as response:
        token = json.load(response)["token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": ", ".join((
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.docker.distribution.manifest.v2+json",
        )),
    }
    missing = []
    for variant in ("builder", "alpine"):
        tag = f"{version}-{variant}"
        url = f"https://registry-1.docker.io/v2/library/caddy/manifests/{tag}"
        request = urllib.request.Request(url, headers=headers, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=30):
                pass
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            missing.append(f"caddy:{tag}")
    return missing


def main():
    caddy = latest_stable(github_items("caddyserver/caddy", "releases"), releases=True)
    cloudflare = latest_stable(github_items("caddy-dns/cloudflare", "tags"))
    missing = missing_caddy_base_images(caddy)
    print(f"Selected Caddy {caddy}; Cloudflare module v{cloudflare}")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as output:
        output.write(f"CADDY_VERSION={caddy}\nCLOUDFLARE_VERSION=v{cloudflare}\n")
        output.write(f"MISSING_CADDY_BASE_IMAGES={' '.join(missing)}\n")


if __name__ == "__main__":
    main()
