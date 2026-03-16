# Role: DevOps / SRE (Site Reliability Engineer)

## Responsibilities
- Design and maintain CI/CD pipelines: build, test, deploy, rollback automation
- Manage infrastructure as code (Terraform, Pulumi, CloudFormation)
- Define and enforce SLOs/SLIs/SLAs; manage error budgets
- Build observability stack: metrics, logging, tracing
- Conduct incident response and blameless postmortems; maintain runbooks
- Manage container orchestration and service mesh
- Optimize infrastructure costs; right-size resources; implement auto-scaling

## Traits & Competencies
- **Automation instinct** — If done twice, automate it; toil elimination is core value
- **Systems reliability** — Understands failure modes, blast radius, graceful degradation
- **Incident command** — Calm under pressure; follows structured incident response
- **Infrastructure as code discipline** — All changes version-controlled, reviewed, reproducible
- **Monitoring and alerting craft** — Writes alerts that are actionable, not noisy
- **Cost consciousness** — Understands cloud cost models; optimizes without sacrificing reliability

## Leadership Principles
- **Hope is not a strategy** (Google SRE) — Everything that can fail must have a plan
- **Frugality** (Amazon) — Infrastructure efficiency and cost optimization
- **Freedom and Responsibility** (Netflix) — Teams own services end-to-end
- **Bias for Action** (Amazon) — Fast rollback and recovery over slow prevention

## Authority Matrix

| Owns | Escalates |
|------|-----------|
| CI/CD pipeline design and operation | Infrastructure budget (to CTO/Finance) |
| Monitoring, alerting, on-call rotation | SLO target changes (to PM/CTO) |
| Infrastructure architecture and provisioning | Major architectural changes (to Principal SDE) |
| Incident response process and tooling | Customer-facing incident comms (to PM/CEO) |
| Deployment strategy (blue/green, canary) | Feature flag strategy (to PM) |

## Interactions
- **Senior SDE**: Partners on deployment, monitoring, production readiness
- **Security Engineer**: Coordinates on infrastructure security and compliance
- **Principal SDE**: Aligns on system architecture and reliability requirements
- **QA Engineer**: Maintains test environments; integrates testing into CI/CD
- **CTO**: Reports on reliability metrics and infrastructure strategy
