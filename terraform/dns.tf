resource "google_dns_managed_zone" "projectptah" {
  name     = "projectptah"
  dns_name = "${var.domain}."
}

# --- Global HTTPS Load Balancer for custom domain ---

resource "google_compute_region_network_endpoint_group" "api" {
  name                  = "samfhir-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.api.name
  }
}

resource "google_compute_backend_service" "api" {
  name                  = "samfhir-api-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.api.id
  }
}

resource "google_compute_url_map" "api" {
  name            = "samfhir-api-urlmap"
  default_service = google_compute_backend_service.api.id
}

resource "google_compute_managed_ssl_certificate" "api" {
  name = "samfhir-api-cert"

  managed {
    domains = ["api.${var.domain}"]
  }
}

resource "google_compute_target_https_proxy" "api" {
  name             = "samfhir-api-https-proxy"
  url_map          = google_compute_url_map.api.id
  ssl_certificates = [google_compute_managed_ssl_certificate.api.id]
}

resource "google_compute_global_address" "api" {
  name = "samfhir-api-ip"
}

resource "google_compute_global_forwarding_rule" "api" {
  name                  = "samfhir-api-forwarding"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_https_proxy.api.id
  ip_address            = google_compute_global_address.api.id
  port_range            = "443"
}

# --- HTTP to HTTPS redirect ---

resource "google_compute_url_map" "api_redirect" {
  name = "samfhir-api-http-redirect"

  default_url_redirect {
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

resource "google_compute_target_http_proxy" "api_redirect" {
  name    = "samfhir-api-http-proxy"
  url_map = google_compute_url_map.api_redirect.id
}

resource "google_compute_global_forwarding_rule" "api_redirect" {
  name                  = "samfhir-api-http-forwarding"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_http_proxy.api_redirect.id
  ip_address            = google_compute_global_address.api.id
  port_range            = "80"
}

# DNS A record pointing to the load balancer IP
resource "google_dns_record_set" "api" {
  name         = "api.${var.domain}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.projectptah.name
  rrdatas      = [google_compute_global_address.api.address]
}
