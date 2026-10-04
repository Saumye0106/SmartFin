#!/bin/bash
# Rolls SmartFin to an image tag that is already in ECR, and goes back to the previous
# tag if the new version does not come up healthy.
#
#   sudo smartfin-deploy <git commit, 7 to 40 hex characters>
#
# Installed by Ansible as /usr/local/bin/smartfin-deploy. The GitHub pipeline runs it through
# SSM Run Command (document "smartfin-deploy"); it can also be run by hand on the server.
# It only changes the image tag: changes to the manifests in infra/k8s still need the playbook.
set -euo pipefail

TAG="${1:-}"
if ! [[ "$TAG" =~ ^[0-9a-f]{7,40}$ ]]; then
  echo "usage: smartfin-deploy <git commit>" >&2
  exit 2
fi

KUBECTL="/usr/local/bin/k3s kubectl"
OVERLAY=/opt/smartfin/k8s/overlays/aws
FILE="$OVERLAY/kustomization.yaml"

# One deploy at a time
exec 9>/var/lock/smartfin-deploy.lock
if ! flock -n 9; then
  echo "another deploy is running" >&2
  exit 1
fi

roll_out() {
  $KUBECTL apply -k "$OVERLAY" &&
    $KUBECTL -n smartfin rollout status deployment/backend --timeout=300s &&
    $KUBECTL -n smartfin rollout status deployment/frontend --timeout=300s &&
    curl -fsS --retry 12 --retry-delay 5 --retry-all-errors -o /dev/null http://127.0.0.1/healthz
}

cp "$FILE" "$FILE.previous"
sed -i -E "s/^([[:space:]]*newTag:[[:space:]]*).*/\1\"$TAG\"/" "$FILE"

# The pull credential lasts 12 hours; renew it so the new images can be fetched.
/usr/local/bin/smartfin-ecr-login > /dev/null

if roll_out; then
  rm -f "$FILE.previous"
  echo "SmartFin $TAG is running"
  exit 0
fi

echo "Rollout of $TAG failed; going back to the previous version" >&2
$KUBECTL -n smartfin get pods >&2 || true
mv "$FILE.previous" "$FILE"
if roll_out; then
  echo "Previous version restored" >&2
else
  echo "Could not restore the previous version: check the server" >&2
fi
exit 1
