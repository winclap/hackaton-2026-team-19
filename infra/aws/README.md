# infra/aws — Hackaton 2026 Grupo 19

Terraform/OpenTofu para los recursos AWS del proyecto. Etapa 1: solo IAM policy
para invocar Claude Haiku 4.5 y Sonnet 4.5 en Bedrock (us-east-1).

## Pre-requisitos

```sh
aws sso login --profile sandbox
aws sts get-caller-identity --profile sandbox   # debe devolver account 727242552949
```

Adicional (one-time, manual): en la consola de Bedrock (us-east-1) →
**Model access** → habilitar acceso a Claude Haiku 4.5 y Claude Sonnet 4.5.
Esto no se puede provisionar por Terraform para foundation models.

## Apply

```sh
cd infra/aws
tofu init
tofu plan
tofu apply
```

## Tags

Todos los recursos llevan `Project=hackaton-2026` y `Group=grupo-19` vía
`default_tags` del provider. La cuenta `sandbox` es compartida con otros
equipos del hackaton, los tags son obligatorios para identificar ownership y
costo.

## Roadmap

- **Etapa 1 (acá)**: IAM policy de invoke Bedrock.
- **Etapa 2**: bucket S3 para `voice_report.json`/`analyses.json`, migrar
  backend Terraform a S3.
- **Etapa 3**: IAM role/instance profile para deploy en compute (Lambda/EC2).
