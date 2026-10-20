# Jellyfin homelab fork

Mac source: `/Volumes/Docker/homelab/repos/apps/jellyfin`.
Owned fork: https://github.com/dez011/jellyfin . Upstream: jellyfin/jellyfin.
Deployment branch `homelab` starts at upstream v12.0, matching production 12.0.
Upstream master is 13.x; do not merge it into production without a separate
web-client/base-image/database compatibility review. The image version gate
deliberately blocks other versions until this compatibility pin is updated.

Native Jenkins `jellyfin-homelab-ci` watches only `homelab`; a push runs the
upstream .NET suite, publishes an immutable local image tagged by exact Git SHA,
backs up stopped Jellyfin configuration, and deploys only YAMS's jellyfin service.
The existing LinuxServer web client, FFmpeg, Intel drivers, volumes, identities,
Traefik route and media paths remain. No service is moved to the Mac.

The CI override is `/srv/homelab/stacks/media/yams/docker-compose.jellyfin-ci.yaml`.
Preserve it in subsequent Compose operations (use all three files in the
container's Compose labels). Backups and previous image IDs are under
`/srv/homelab/archive/jellyfin-ci`; never delete media or volumes for rollback.
Health verifies HTTP readiness and exact runtime image, not actual playback.
If a migration ever changes the DB, stop and review restoring the stopped
configuration archive; switching to an older image alone is not a DB rollback.

The existing daily Mac upstream scout discovers this checkout and its upstream
remote automatically. Its `homelab.upstreamRef` Git setting selects
`refs/heads/release-12.z` so stable 12.x changes, not 13.x development, are scanned.
Update notices go to Matrix Hermes Updates; incidents go
to IT — Incidents. An update notice does not merge or deploy source.
