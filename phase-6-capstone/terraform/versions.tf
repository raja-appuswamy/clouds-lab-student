# Provider pins (provided). Terraform itself is preinstalled in Cloud Shell.
terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
  # Task 1: the agent (and Terraform) act as a dedicated, bounded service account — no key
  # file; your own credentials mint short-lived tokens for it. That bound is the phase.
  impersonate_service_account = var.impersonate
}
