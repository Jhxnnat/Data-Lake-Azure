variable "subscription_id" {
  description = "Azure subscription id"
  type        =  string
  sensitive   = true
}

variable "resource_group_name" {
	description = "name of resource group"
	type        = string
}

variable "location" {
	description = "location of the resource group"
	type        = string
	default     = "East US"
}

variable "storage_account_name" {
	description = "name of the storage account"
	type        = string
}

variable "eventhub_namespace_name" {
  description = "name of evenhub namespace"
  type        = string
}

