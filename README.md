# Plataforma de Datos con Data Lake y Procesamiento en Tiempo Real en Azure

> [!NOTE]
> Trabajo en progreso

Plataforma de datos sobre Azure: un Data Lake en Azure Data Lake Storage Gen2 estructurado en capas (Bronze/Silver/Gold), ingesta de eventos en tiempo real con Azure Event Hubs, procesamiento de streams con Azure Stream Analytics, y consultas analíticas sobre Azure Synapse Analytics.
El pipeline CI/CD en Azure Pipelines automatiza el despliegue de infraestructura y transformaciones de datos.


## Requirements
- Azure account
- Azure cli
- Terraform
- Python 3+

## Running

`az login`

`terraform init`
`terraform apply`

Stream analytics are created and stopped explicitly with the Azure CLI stream analytics extension (or in Azure portal), see: https://github.com/Azure/azure-cli-extensions/blob/main/src/stream-analytics/README.md

`az stream-analytics job start --resource-group [GROUP] --name [NAME] --output-start-mode JobStartTime`

Stopping:
`az stream-analytics job stop --resource-group [GROUP] --name [NAME]`

Generator script:
`pip install -r requirements.txt`

Examples of running generator locally:
`python scripts/generator.py --mode stdout --interval 0.01`
`python scripts/generator.py --mode stdout --count 1000 --interval 1`

To run with Azure set EVENT_HUB_CONNECTION_STRING and EVENTHUB_NAME, can be taken from terraform output with `terraform output`


`python scripts/generator.py --mode eventhub --interval 1`

To monitor what is happening, in Azure portal

