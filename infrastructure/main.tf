provider "azurerm" {
	features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "datalake" {
	name                     = var.storage_account_name
	resource_group_name      = azurerm_resource_group.main.name
	location                 = azurerm_resource_group.main.location
	account_tier             = "Standard"
	account_replication_type = "LRS"
	account_kind             = "StorageV2"
	is_hns_enabled           = "true" # activar el hierarchical namespace
}

## contenedores para la arquitectura medallón
resource "azurerm_storage_data_lake_gen2_filesystem" "bronze" {
  name               = "bronze"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "silver" {
  name               = "silver"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "gold" {
  name               = "gold"
  storage_account_id = azurerm_storage_account.datalake.id
}

## Lifecycle policy para contenedor bronce
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.datalake.id
  rule {
    name   = "bronze-policy"
    enable = true
    filters {
      prefix_match = ["bronze/"]
      blob_types   = ["blockBlob"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 90
        tier_to_archive_after_days_since_modification_greater_than = 365
      }
    }
  }
}
