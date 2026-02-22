resource "google_artifact_registry_repository" "api" {
  location      = var.region
  repository_id = "samfhir"
  description   = "SamFHIR container images"
  format        = "DOCKER"
}
