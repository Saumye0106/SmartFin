#!/usr/bin/env bash
# Writes inventory.ini and vars.yml for the playbook from the Terraform outputs.
# Run after `terraform apply`:   ./from_terraform.sh [path-to-ssh-private-key]
set -euo pipefail

cd "$(dirname "$0")"
KEY="${1:-$HOME/.ssh/smartfin}"
# Inside WSL, Terraform is the Windows program: run with TERRAFORM=terraform.exe
TERRAFORM="${TERRAFORM:-terraform}"
out() { "$TERRAFORM" -chdir=../terraform output -raw "$1" | tr -d '\r'; }

IP="$(out node_public_ip)"

cat > inventory.ini <<EOF
[node]
smartfin ansible_host=${IP} ansible_user=ubuntu ansible_ssh_private_key_file=${KEY}
EOF

cat > vars.yml <<EOF
node_public_ip: "${IP}"
aws_region: "$(out region)"
ecr_registry: "$(out ecr_registry)"
uploads_bucket: "$(out uploads_bucket)"
ssm_parameter_prefix: "$(out ssm_parameter_prefix)"
EOF

echo "Wrote inventory.ini and vars.yml for ${IP}"
