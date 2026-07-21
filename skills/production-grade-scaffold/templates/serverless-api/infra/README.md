# Infrastructure as Code (serverless)

IaC here is the serverless.yml / SAM template / CDK stack itself, not generic
Terraform+Kubernetes - the platform owns the runtime. Still apply: remote state (if using CDK/
Terraform alongside), least-privilege IAM per function, and no manual console changes to what's
defined here. See references/architecture-archetypes.md #3 and references/infrastructure-delivery.md.
