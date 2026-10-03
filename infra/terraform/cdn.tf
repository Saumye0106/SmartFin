# HTTPS without owning a domain: CloudFront gives the site a free https://<id>.cloudfront.net address
# with an AWS-managed certificate, and forwards requests to the server.
#
#   browser ──HTTPS──► CloudFront ──HTTP──► server (port 80, open to CloudFront only)
#
# The hop from CloudFront to the server is plain HTTP: encrypting it needs a certificate on the
# server, which needs a domain name. The server's port 80 accepts connections only from
# CloudFront's address ranges (see network.tf), so the site cannot be reached around it.

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

# Pass every header (including Authorization), cookie and query string through to the app.
data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewer"
}

# Adds Strict-Transport-Security (always use HTTPS), X-Content-Type-Options, X-Frame-Options and
# Referrer-Policy to every response.
data "aws_cloudfront_response_headers_policy" "security" {
  name = "Managed-SecurityHeadersPolicy"
}

resource "aws_cloudfront_distribution" "site" {
  enabled         = true
  comment         = "${var.name} site"
  is_ipv6_enabled = true
  http_version    = "http2and3"
  price_class     = "PriceClass_200" # includes India; skips the most expensive regions

  origin {
    origin_id = "node"
    # CloudFront needs a host name, not an IP address: this is the Elastic IP's public DNS name.
    domain_name = aws_eip.node.public_dns

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_read_timeout      = 60
      origin_keepalive_timeout = 5
    }
  }

  # Pages and API calls: never cached, everything forwarded.
  default_cache_behavior {
    target_origin_id           = "node"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id   = data.aws_cloudfront_origin_request_policy.all_viewer.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security.id
    compress                   = true
  }

  # Built JavaScript and CSS have a content hash in their names, so they can be cached at the edge.
  ordered_cache_behavior {
    path_pattern               = "/assets/*"
    target_origin_id           = "node"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = data.aws_cloudfront_cache_policy.optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security.id
    compress                   = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
