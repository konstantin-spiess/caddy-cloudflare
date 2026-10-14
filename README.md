# Caddy with Cloudflare DNS

Official Caddy Docker image with [`caddy-dns/cloudflare`](https://github.com/caddy-dns/cloudflare), built for `linux/amd64`.

## Usage

Use a combined version tag in your Compose service:

```yaml
image: ghcr.io/konstantin-spiess/caddy-cloudflare:2.11.7-cf.0.2.4
```

This means **Caddy 2.11.7 + Cloudflare module 0.2.4**. Mount your configuration at `/etc/caddy` and persist `/data` and `/config`. The image contains no site configuration, credentials or certificates.

| Tag | Purpose |
| --- | --- |
| `<caddy>-cf.<module>` | Readable component versions |
| `stable` | Latest tested build |
| `<caddy>-cf<module>-build<run>-<attempt>` | Retained build for rollback |

## Updates

GitHub Actions checks stable Caddy releases and Cloudflare module tags independently each day. New versions and pushes to `main` trigger a build. Before publishing, it checks the actual versions, validates a minimal configuration and tests an HTTP response. Validate your own configuration before deployment; publishing does not update your server.

For base-image updates with unchanged component versions, run the workflow manually with **force** enabled. The daily check detects component-version changes only. Version tags may be rebuilt; use a unique build tag or digest to pin an exact image.

GitHub may delay scheduled runs or disable them after 60 days of repository inactivity; see [scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## WUD

For WUD 9.4.1, use the combined version tag above with these Compose service labels:

```yaml
labels:
  wud.watch: "true"
  wud.tag.include: '^[0-9]+\.[0-9]+\.[0-9]+-cf\.[0-9]+\.[0-9]+\.[0-9]+$$'
  wud.watch.digest: "true"
```

The filter accepts component-version tags only; `$$` escapes Compose interpolation. Digest watching also detects rebuilds with unchanged versions. Configure your WUD update triggers separately.

WUD can classify a module-only update as a SemVer prerelease change because of the `-cf.` suffix; the selected upstream versions are stable.

## Build locally

```bash
docker build --pull \
  --build-arg CADDY_VERSION=2.11.7 \
  --build-arg CLOUDFLARE_VERSION=v0.2.4 \
  --tag caddy-cloudflare:local .
```
