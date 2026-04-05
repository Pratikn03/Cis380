# Terraform Infrastructure Scaffold

## Purpose
Define AWS-native infrastructure scaffolding for Sentifargo deployment environments.

## Scope
- ECS service scaffolds
- ALB ingress
- RDS PostgreSQL
- S3 upload bucket support
- EventBridge + SQS backbone

## Run locally
```bash
cd infra/terraform
terraform init
terraform plan -var='environment=dev'
```

## Test and quality commands
```bash
terraform validate
python3 scripts/quality/docs_quality_check.py --mode fast --threshold 85
```

## Ownership and canonical links
- Owner: Sentifargo Infra Team
- Last verified: 2026-02-11
- Canonical docs index: `../../docs/README.md`
- Canonical source map: `../../docs/CANONICAL.md`
