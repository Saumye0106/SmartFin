# SmartFin on AWS

One EC2 server running Kubernetes (k3s), PostgreSQL on RDS, images in ECR, profile pictures in S3.
Terraform creates the AWS resources, Ansible sets up the server, Kubernetes runs the app.

```
browser ──► Elastic IP ──► EC2 (k3s)
                            ├─ frontend pods (nginx: site + forwards API calls)
                            └─ backend pods  ──► RDS PostgreSQL (private subnets)
                                             ──► S3 (profile pictures)
                                             ──► Bedrock (optional)
```

## Cost

Everything below bills by the hour from the moment `terraform apply` finishes until `terraform destroy`.
Rough monthly figures for ap-south-1, from memory; check the [AWS pricing calculator](https://calculator.aws/) before relying on them.

| Item | About |
|---|---|
| EC2 t3.small (t3.medium is about double) | $15 |
| 30 GB disk | $3 |
| Public IPv4 address | $4 |
| RDS db.t4g.micro + 20 GB | $16 |
| ECR, S3, Parameter Store | under $1 |
| **Total** | **about $40/month** |

New AWS accounts get some of this free for 12 months (EC2 and RDS micro sizes).

## Before the first run

1. **AWS credentials for this project.** The credentials must be allowed to manage EC2, VPC, RDS, ECR, S3, IAM
   (roles, instance profiles, policies) and SSM Parameter Store. Create a dedicated IAM user or role for it and
   configure it as its own CLI profile, so it doesn't replace any other project's credentials:

   ```
   aws configure --profile smartfin
   ```

2. **An SSH key** for logging in to the server:

   ```
   ssh-keygen -t ed25519 -f ~/.ssh/smartfin
   ```

3. **Your settings**: copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and fill in the
   profile, your public IP (`curl https://checkip.amazonaws.com`) and the contents of `~/.ssh/smartfin.pub`.
   If your IP changes, update `admin_cidr` and apply again.

## Create

```
cd infra/terraform
terraform init
terraform plan      # read what it will create; nothing is created yet
terraform apply     # creates it; billing starts
```

RDS takes 5 to 10 minutes. The outputs list the server address, the ECR repositories and the bucket name.

## Deploy the app

Three steps: push the images, then let Ansible set up the server and roll the app out.
Ansible does not run on Windows itself, so run the last step inside WSL (Ubuntu).

```
# 1. Build and push both images, tagged with the current commit (Git Bash or PowerShell, Docker running)
cd infra/terraform
REGISTRY=$(terraform output -raw ecr_registry)
TAG=$(git rev-parse --short HEAD)
aws ecr get-login-password --region ap-south-1 --profile smartfin | docker login --username AWS --password-stdin $REGISTRY
docker build -t $REGISTRY/smartfin-backend:$TAG  ../../backend  && docker push $REGISTRY/smartfin-backend:$TAG
docker build -t $REGISTRY/smartfin-frontend:$TAG ../../frontend && docker push $REGISTRY/smartfin-frontend:$TAG

# 2. In WSL: copy the SSH key into WSL once (keys on the Windows drive have permissions ssh refuses)
mkdir -p ~/.ssh && cp /mnt/c/Users/<you>/.ssh/smartfin ~/.ssh/smartfin && chmod 600 ~/.ssh/smartfin

# 3. In WSL: set up the server and deploy
cd /mnt/c/Users/<you>/smartfin-copy/smartfin-copy/infra/ansible
TERRAFORM=terraform.exe ./from_terraform.sh ~/.ssh/smartfin
~/.venvs/smartfin-ansible/bin/ansible-playbook -i inventory.ini site.yml -e image_tag=<the TAG from step 1>
```

Ansible has to be recent enough for the Python it runs on (ansible-core 2.15 fails on Python 3.14 with
"module 'ast' has no attribute 'Str'"). A separate environment avoids touching the system packages:

```
python3 -m venv --without-pip ~/.venvs/smartfin-ansible
curl -sS https://bootstrap.pypa.io/get-pip.py | ~/.venvs/smartfin-ansible/bin/python3
~/.venvs/smartfin-ansible/bin/pip install ansible-core
```

The playbook installs k3s, copies the app's secrets from Parameter Store into the cluster, sets up the ECR
login refresh, applies the manifests in `infra/k8s`, waits for the rollout and checks the site answers.
Run it again with a new `image_tag` to deploy a new version; the rollout replaces one copy at a time.

To try the same manifests on your own machine first, without AWS:
`kubectl apply -k infra/k8s/overlays/local` on any local cluster that has the two images loaded.

This has been run for real: first deployed on 2026-10-04 (41 resources, then the playbook) and checked from
outside: the site, sign-up and login, the risk score, profile pictures through S3, and that the database and
the backend port are not reachable from the internet.

## Destroy

```
cd infra/terraform
terraform destroy
```

This removes everything, including the database and the uploaded pictures (the practice settings skip the final
database snapshot). Set `db_deletion_protection = true` and `db_skip_final_snapshot = false` once the data matters.

## Things to know

- `terraform.tfstate` contains the database password and the login-signing secret in plain text. It is git-ignored;
  keep it off shared drives. `versions.tf` shows how to move it to a private S3 bucket.
- SSH (22) and the Kubernetes API (6443) are open only to `admin_cidr`. Ports 80 and 443 are open to everyone.
- The database is not reachable from the internet, only from the server.
- No access keys are stored on the server: it gets its permissions (ECR pull, the uploads bucket, the app's
  secrets, Bedrock) from an IAM role.
- The site is served over plain HTTP until a domain and certificate are added.
