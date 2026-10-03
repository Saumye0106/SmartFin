# The k3s node: one Ubuntu server with a fixed public address. Ansible installs k3s on it.

data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_key_pair" "admin" {
  key_name   = "${var.name}-admin"
  public_key = var.ssh_public_key
}

resource "aws_instance" "node" {
  ami                    = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.node.id]
  key_name               = aws_key_pair.admin.key_name
  iam_instance_profile   = aws_iam_instance_profile.node.name

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_gb
    encrypted   = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required" # IMDSv2 only
    # 2 hops so that pods (one network hop further than the host) can obtain the node's role
    # credentials for S3, ECR and Bedrock.
    http_put_response_hop_limit = 2
  }

  # A newer Ubuntu image must not replace a running server on the next apply.
  lifecycle {
    ignore_changes = [ami]
  }

  tags = { Name = "${var.name}-node" }
}

resource "aws_eip" "node" {
  domain   = "vpc"
  instance = aws_instance.node.id

  tags = { Name = "${var.name}-node" }

  depends_on = [aws_internet_gateway.main]
}
