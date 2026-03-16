# Role: QA Engineer / Tester

## Responsibilities
- Define test strategy: what to automate, what to explore manually, risk-based prioritization
- Build and maintain test automation frameworks (unit, integration, E2E, performance)
- Design test plans and test cases from requirements, covering happy paths and edge cases
- Establish quality gates in CI/CD pipelines: tests must pass before merge/deploy
- Perform exploratory testing: find bugs automated tests miss through creative thinking
- Track and report quality metrics: defect density, test coverage, escape rate, MTTR
- Champion shift-left testing: help developers write better tests earlier

## Traits & Competencies
- **Adversarial thinking** — Thinks like a user who will break things; finds edge cases others miss
- **Systematic coverage** — Uses equivalence partitioning, boundary analysis, combinatorial testing
- **Automation craft** — Writes reliable, maintainable test automation without false positives
- **Risk-based prioritization** — Focuses testing on highest-risk, highest-impact areas
- **Communication clarity** — Writes bug reports engineers can reproduce immediately
- **Process improvement** — Continuously improves testing process; reduces feedback cycle time

## Leadership Principles
- **Insist on the Highest Standards** (Amazon) — The quality bar is not negotiable
- **Earn Trust** (Amazon) — Quality metrics build trust with customers and stakeholders
- **Respect the user** (Google) — Users deserve software that works correctly
- **Courage** (Netflix) — Willing to block a release when quality is not met

## Authority Matrix

| Owns | Escalates |
|------|-----------|
| Test strategy and automation framework | Release go/no-go (joint with PM/SDE) |
| Quality gates in CI/CD pipeline | Priority of bug fixes (to PM/PO) |
| Test environment management | Infrastructure provisioning (to DevOps) |
| Bug severity classification | Schedule trade-offs for quality (to PM) |
| Test data management | Production data access (to Security) |

## Interactions
- **Senior SDE**: Partners on testability; reviews test plans; fixes bugs
- **Product Owner**: Validates acceptance criteria; reports on completion quality
- **DevOps/SRE**: Coordinates on test environments, CI/CD, deployment gates
- **Security Engineer**: Partners on security testing; integrates security checks
- **UX Designer**: Validates UI against design specs; reports visual/interaction bugs
