variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "domain" {
  description = "Domain name for DNS zone"
  type        = string
}

variable "image" {
  description = "Container image for Cloud Run"
  type        = string
  default     = "australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest"
}
