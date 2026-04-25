terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the domain"
  type        = string
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "subdomain" {
  description = "Subdomain to expose the app on"
  type        = string
  default     = "hackaton"
}

variable "domain" {
  description = "Root domain (e.g. lucagelmini.ar)"
  type        = string
}

variable "local_port" {
  description = "Local port where the web app runs (Vite dev server)"
  type        = number
  default     = 5173
}

resource "random_password" "tunnel_secret" {
  length  = 32
  special = false
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "tunnel" {
  account_id = var.cloudflare_account_id
  name       = "hackaton-local"
  secret     = base64encode(random_password.tunnel_secret.result)
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "tunnel_config" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.tunnel.id

  config {
    ingress_rule {
      hostname = "${var.subdomain}.${var.domain}"
      service  = "http://localhost:${var.local_port}"
    }
    ingress_rule {
      service = "http_status:404"
    }
  }
}

resource "cloudflare_record" "tunnel_dns" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  content = "${cloudflare_zero_trust_tunnel_cloudflared.tunnel.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.tunnel.id
}

output "tunnel_token" {
  value     = cloudflare_zero_trust_tunnel_cloudflared.tunnel.tunnel_token
  sensitive = true
}

output "public_url" {
  value = "https://${var.subdomain}.${var.domain}"
}
