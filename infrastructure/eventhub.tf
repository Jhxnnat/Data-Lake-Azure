## generador de eventos
resource "azurerm_eventhub_namespace" "evh_namespace" {
  name                = var.eventhub_namespace_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  capacity            = 1
}

resource "azurerm_eventhub" "eventhub" {
  name              = "telemetry"
  namespace_id      = azurerm_eventhub_namespace.evh_namespace.id
  partition_count   = 4
  message_retention = 7
}

resource "azurerm_eventhub_authorization_rule" "evh_auth" {
  name                = "eventhub_auth"
  namespace_name      = azurerm_eventhub_namespace.evh_namespace.name
  eventhub_name       = azurerm_eventhub.eventhub.name
  resource_group_name = azurerm_resource_group.main.name
  listen = true
  send   = true
  manage = true
}

