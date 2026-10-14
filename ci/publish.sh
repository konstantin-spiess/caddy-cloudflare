#!/usr/bin/env bash
set -euo pipefail

image="ghcr.io/${GITHUB_REPOSITORY,,}"
versions="${CADDY_VERSION}-cf${CLOUDFLARE_VERSION#v}"
build_tag="${versions}-build${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
candidate="local/caddy-ci:${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
smoke_container="caddy-smoke-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
test_config="${RUNNER_TEMP}/Caddyfile-smoke"

cleanup() {
    docker rm -f "$smoke_container" >/dev/null 2>&1 || true
    docker logout ghcr.io >/dev/null 2>&1 || true
}
trap cleanup EXIT

printf '%s' "$GH_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

if [ "${FORCE_REBUILD:-false}" != true ]; then
    if docker pull "$image:stable"; then
        installed_versions=$(docker inspect "$image:stable" --format '{{index .Config.Labels "org.opencontainers.image.version"}}')
        if [ "$installed_versions" = "$versions" ]; then
            printf 'No new component versions: %s\n' "$versions" >> "$GITHUB_STEP_SUMMARY"
            exit 0
        fi
    else
        printf 'Existing stable image unavailable; attempting a fresh build.\n'
    fi
fi

docker build --pull --platform linux/amd64 \
    --build-arg "CADDY_VERSION=$CADDY_VERSION" \
    --build-arg "CLOUDFLARE_VERSION=$CLOUDFLARE_VERSION" \
    --label "org.opencontainers.image.source=https://github.com/$GITHUB_REPOSITORY" \
    --label "org.opencontainers.image.revision=$GITHUB_SHA" \
    --label "org.opencontainers.image.version=$versions" \
    --tag "$candidate" .

actual_version=$(docker run --rm --network none --entrypoint /usr/bin/caddy "$candidate" version)
test "${actual_version%% *}" = "v$CADDY_VERSION"
modules=$(docker run --rm --network none --entrypoint /usr/bin/caddy "$candidate" list-modules --skip-standard --versions)
printf '%s\n' "$modules"
printf '%s\n' "$modules" | awk -v wanted="$CLOUDFLARE_VERSION" '
    $1 == "dns.providers.cloudflare" && $2 == wanted { found = 1 }
    END { exit !found }
'

printf '{\nauto_https off\n}\n:80 {\nrespond "caddy-ok" 200\n}\n' > "$test_config"
docker run --rm --network none --entrypoint /usr/bin/caddy \
    --mount "type=bind,src=$test_config,dst=/etc/caddy/Caddyfile,readonly" \
    "$candidate" validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker run -d --name "$smoke_container" --network none \
    --mount "type=bind,src=$test_config,dst=/etc/caddy/Caddyfile,readonly" \
    "$candidate"

ready=false
for attempt in {1..15}; do
    if response=$(docker exec "$smoke_container" wget -q -T 2 -O - http://127.0.0.1/); then
        if [ "$response" = caddy-ok ]; then
            ready=true
            break
        fi
    fi
    sleep 1
done
if [ "$ready" != true ]; then
    docker logs "$smoke_container"
    exit 1
fi

# Publish stable only after every check, retaining a unique tag for rollback.
docker tag "$candidate" "$image:$build_tag"
docker push "$image:$build_tag"
docker tag "$candidate" "$image:stable"
docker push "$image:stable"
printf 'Published `%s:stable`\n\nVersions: `%s`\n\nRetained tag: `%s:%s`\n' \
    "$image" "$versions" "$image" "$build_tag" >> "$GITHUB_STEP_SUMMARY"
