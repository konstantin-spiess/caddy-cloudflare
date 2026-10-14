# Caddy with Cloudflare DNS

Caddy image built from the official Caddy Docker images with
[`caddy-dns/cloudflare`](https://github.com/caddy-dns/cloudflare).

```text
ghcr.io/konstantin-spiess/caddy-cloudflare:stable
```

Each build also publishes a readable component-version tag, for example:

```text
ghcr.io/konstantin-spiess/caddy-cloudflare:2.11.7-cf.0.2.4
```

The first three numbers identify Caddy; `cf.0.2.4` identifies the Cloudflare
module. A module-only update changes this to e.g. `2.11.7-cf.0.2.5`.

The image contains no site configuration, credentials or certificates.
Mount your own configuration and persistent Caddy state at deployment time.
The current build targets `linux/amd64`.

## Updates

GitHub Actions checks published stable Caddy releases and stable Cloudflare
module tags independently, daily at 06:23 UTC. When either version changes, it
builds a new image. Prereleases and draft releases are excluded.

Before publishing, the workflow checks the actual Caddy and module versions,
validates a minimal configuration and tests an HTTP response in an isolated
container. These checks do not validate a user's production configuration.

Each successful build receives a unique tag:

```text
<caddy>-cf<module>-build<workflow-run-id>-<attempt>
```

Only after the checks pass is `stable` updated. Previous build tags are retained
as deployment rollback targets. The combined component versions are also stored
in the OCI label `org.opencontainers.image.version` and the workflow summary.

For readable updates in [WUD](https://getwud.app/docs/configuration/watchers/labels/),
deploy a component-version tag and restrict candidate tags to this format.
The following are service labels in Docker Compose; `$$` escapes Compose's
interpolation and becomes a single `$` in the actual container label:

```yaml
labels:
  wud.watch: "true"
  wud.tag.include: '^[0-9]+\.[0-9]+\.[0-9]+-cf\.[0-9]+\.[0-9]+\.[0-9]+$$'
  wud.watch.digest: "true"
```

This excludes `stable` and the separate build tags from version candidates.
WUD 9.4.1 preserves the suffix and compares these version tags numerically;
no tag transformation is needed. The `-cf.` suffix is formally a SemVer
prerelease field, but the upstream selector includes only stable releases/tags;
it does not mean this image contains a Caddy prerelease. WUD may classify a
module-only update as a prerelease change; this is not a Caddy patch update.
Digest monitoring remains useful for forced rebuilds of the same component
versions, for example to refresh base images. `stable` remains available as an
alternative mutable alias. Building and publishing does not install anything
on a server. Configure the existing WUD triggers separately before deployment.

Changes on `main` rebuild the image. To refresh base images without changing
component versions, start the workflow manually with `force` enabled. The daily
version check alone does not detect base-image-only changes.

Scheduled workflows can be delayed. GitHub may disable scheduled workflows in
public repositories after 60 days without repository activity; see
[GitHub's schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Manual execution remains available.

## Build locally

```bash
docker build --pull \
  --build-arg CADDY_VERSION=2.11.7 \
  --build-arg CLOUDFLARE_VERSION=v0.2.2 \
  --tag caddy-cloudflare:local .
```

## Package visibility

New GHCR packages are initially private. To allow anonymous downloads, change
the package's visibility to public separately from the repository's visibility.
See [GitHub Container Registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
