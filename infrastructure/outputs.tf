output "resource_group_name" {
  description = "nombre del resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "nombre del storage account"
  value       = azurerm_storage_account.datalake.name
}

output "eventhub_connection_string" {
  value     = azurerm_eventhub_authorization_rule.evh_auth.primary_connection_string
  sensitive = true
}

