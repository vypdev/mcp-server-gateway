# Coolify and Docker reference

The production gateway is **not** deployed inside Coolify or Docker. It runs natively on the host it manages as a systemd service. See [`native-deployment.md`](native-deployment.md).

Docker bridge networking is not used as the host-control mechanism and does not span hosts. Do not mount `/var/run/docker.sock` into a gateway container as a shortcut: it can grant near-root control of the host and is outside the supported native deployment model.

The repository's Docker files are retained only for isolated development and CI experiments. They are not the recommended production path.
