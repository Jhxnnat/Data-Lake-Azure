resource "azurerm_stream_analytics_job" "analytics" {
  name                                     = "analytics"
  resource_group_name                      = azurerm_resource_group.main.name
  location                                 = azurerm_resource_group.main.location
  compatibility_level                      = "1.2"
  data_locale                              = "en-US"
  events_late_arrival_max_delay_in_seconds = 60
  events_out_of_order_max_delay_in_seconds = 50
  events_out_of_order_policy               = "Adjust"
  output_error_policy                      = "Drop"
  streaming_units                          = 3
  sku_name                                 = "Standard"

  transformation_query = file("${path.module}/query.saql")
}

## stream analytics inputs
resource "azurerm_stream_analytics_stream_input_eventhub" "asa_inputs" {
  name                      = "evh-input-simulation"
  resource_group_name       = azurerm_resource_group.main.name
  stream_analytics_job_name = azurerm_stream_analytics_job.analytics.name
  eventhub_name             = azurerm_eventhub.eventhub.name
  servicebus_namespace      = azurerm_eventhub_namespace.evh_namespace.name
  shared_access_policy_key  = azurerm_eventhub_authorization_rule.evh_auth.primary_key
  shared_access_policy_name = azurerm_eventhub_authorization_rule.evh_auth.name

  serialization {
    type = "Json"
  }
}

## silver container outputs
resource "azurerm_stream_analytics_output_blob" "asa_output" {
  name                      = "silver-output"
  stream_analytics_job_name = azurerm_stream_analytics_job.analytics.name
  resource_group_name       = azurerm_resource_group.main.name
  storage_account_name      = azurerm_storage_account.datalake.name
  storage_account_key       = azurerm_storage_account.datalake.primary_access_key
  storage_container_name    = azurerm_storage_data_lake_gen2_filesystem.silver.name
  path_pattern              = "telemetry/{date}/{time}"
  date_format               = "yyyy/MM/dd"
  time_format               = "HH"

  serialization {
    type            = "Json"
    format          = "LineSeparated"
  }
}

## silver alerts
resource "azurerm_stream_analytics_output_blob" "asa_output_alerts" {
  name                      = "silver-alert-output"
  stream_analytics_job_name = azurerm_stream_analytics_job.analytics.name
  resource_group_name       = azurerm_resource_group.main.name
  storage_account_name      = azurerm_storage_account.datalake.name
  storage_account_key       = azurerm_storage_account.datalake.primary_access_key
  storage_container_name    = azurerm_storage_data_lake_gen2_filesystem.silver.name
  path_pattern              = "alerts/{date}/{time}"
  date_format               = "yyyy/MM/dd"
  time_format               = "HH"

  serialization {
    type            = "Json"
    format          = "LineSeparated"
  }
}

