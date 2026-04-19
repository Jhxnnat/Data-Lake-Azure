# Requirements

## ADLS Gen2, Terraform
- [x] Storage Account con Hierarchical Namespace habilitado.
- [x] Contenedores: bronze, silver, gold con ACLs por capa.
- [x] Lifecycle policy: bronze data > 90 días →  Cool tier; > 365 días → Archive.
- [ ] Private Endpoint para acceso seguro desde Synapse y Data Factory.

## Event Hubs + Stream Analytics
- [x] Event Hubs Namespace con Hub de 4 particiones, retención 7 días.
- [x] Script Python generador de eventos (simula telemetría IoT cada segundo).
- [x] Stream Analytics Job: consumir Event Hubs → calcular promedio/máximo por ventana de 1 minuto → escribir resultados en Silver Layer.
- [x] Alerta: cuando valor métrica excede umbral → escribir en tabla de alertas.

## Azure Synapse Analytics
- [ ] Synapse Workspace con Serverless SQL Pool apuntando a Gold Layer.
- [ ] Vistas SQL sobre datos Parquet en ADLS Gen2.
- [ ] Al menos 3 consultas analíticas de ejemplo: tendencias, top-N, agregaciones.
- [ ] Integración con Azure Monitor para métricas de query performance.

## Data Factory Batch Pipeline
- [ ] Pipeline ADF: copy activity de blob source (CSV) → Bronze Layer (Parquet).
- [ ] Activity de transformación: Bronze → Silver (limpiar nulos, normalizar fechas).
- [ ] Trigger: schedule diario a las 2:00 AM.

# Initial pieces
- [ ] network
- [ ] synapse
- [ ] data factory 
- [x] event hubs
- [x] stream analytics
