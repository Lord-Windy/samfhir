output "nameservers" {
  description = "Nameservers for DNS zone (update registrar to these)"
  value       = google_dns_managed_zone.projectptah.name_servers
}

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "redis_host" {
  description = "Redis instance host (private IP)"
  value       = google_redis_instance.redis.host
}
