# One VPC, two availability zones.
#   public subnets   - the k3s node (it needs to be reachable from the internet)
#   private subnets  - the database only; they have no route to the internet at all
# There is no NAT gateway (about $30/month): nothing in the private subnets needs to call out.

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = var.name }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = var.name }
}

resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = false

  tags = { Name = "${var.name}-public-${local.azs[count.index]}" }
}

resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 10)
  availability_zone = local.azs[count.index]

  tags = { Name = "${var.name}-private-${local.azs[count.index]}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.name}-public" }
}

resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private subnets keep the VPC's default route table, which only has the local route.

# ── Security groups ──────────────────────────────────────────────────────────

resource "aws_security_group" "node" {
  name        = "${var.name}-node"
  description = "k3s node: web traffic from anywhere, administration from one address" # description is immutable; web traffic is now CloudFront only
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.name}-node" }
}

# The addresses CloudFront connects from. AWS maintains this list.
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

# Web traffic reaches the server only through CloudFront (cdn.tf), which is where HTTPS ends.
# Note: this list counts as about 55 rules against the limit of 60 per security group.
resource "aws_vpc_security_group_ingress_rule" "node_http" {
  security_group_id = aws_security_group.node.id
  description       = "HTTP from CloudFront only"
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront.id
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "node_ssh" {
  security_group_id = aws_security_group.node.id
  description       = "SSH from the administrator only"
  cidr_ipv4         = var.admin_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "node_kube_api" {
  security_group_id = aws_security_group.node.id
  description       = "Kubernetes API from the administrator only"
  cidr_ipv4         = var.admin_cidr
  ip_protocol       = "tcp"
  from_port         = 6443
  to_port           = 6443
}

resource "aws_vpc_security_group_egress_rule" "node_all" {
  security_group_id = aws_security_group.node.id
  description       = "Outbound: image pulls, package updates, AWS APIs, the database"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "database" {
  name        = "${var.name}-database"
  description = "PostgreSQL, reachable only from the k3s node"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.name}-database" }
}

resource "aws_vpc_security_group_ingress_rule" "database_from_node" {
  security_group_id            = aws_security_group.database.id
  description                  = "PostgreSQL from the k3s node"
  referenced_security_group_id = aws_security_group.node.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}
