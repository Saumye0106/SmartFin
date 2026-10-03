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
