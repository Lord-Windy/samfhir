resource "google_dns_managed_zone" "projectptah" {
  name     = "projectptah"
  dns_name = "${var.domain}."
}

resource "google_dns_record_set" "api" {
  name         = "api.${var.domain}."
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.projectptah.name
  rrdatas      = [trimsuffix(google_cloud_run_v2_service.api.uri, "/")]
}
