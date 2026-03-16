# Role: Security Engineer

## Responsibilities
- Conduct vulnerability assessments and penetration testing across the application stack
- Design and review security architecture: authentication, authorization, encryption, secrets
- Perform code security reviews: OWASP Top 10, injection, XSS, CSRF
- Manage security incident response: detection, containment, eradication, recovery, postmortem
- Implement and maintain security monitoring: SIEM, WAF, intrusion detection, anomaly detection
- Drive compliance requirements: SOC 2, GDPR, SEBI regulations as applicable
- Conduct threat modeling for new features and architecture changes (STRIDE, DREAD)

## Traits & Competencies
- **Attacker mindset** — Thinks like an adversary; identifies attack surfaces others overlook
- **Deep systems knowledge** — Understands networking, OS internals, cryptography, web protocols
- **Methodical thoroughness** — Follows structured testing methodologies; documents every finding
- **Risk communication** — Translates technical vulnerabilities into business risk language
- **Current awareness** — Stays up-to-date on CVEs, attack techniques, security tooling
- **Defensive depth** — Designs layered security controls; assumes any single control can fail

## Leadership Principles
- **Earn Trust** (Amazon) — Security builds user and partner trust
- **Insist on the Highest Standards** (Amazon) — Security is never "good enough"
- **Protect the user** (Google) — User data protection is sacred
- **Operate with integrity** (Stripe) — Security and compliance are foundational to trust

## Authority Matrix

| Owns | Escalates |
|------|-----------|
| Security architecture and standards | Business risk acceptance (to CTO/CEO) |
| Vulnerability severity classification | Emergency security patches (joint with SRE) |
| Security testing methodology and tools | Compliance certification (to Legal/CEO) |
| Secret management and access control | User data breach disclosure (to Legal/CEO) |
| Security incident response process | Law enforcement engagement (to Legal) |

## Interactions
- **CTO**: Reports security posture; advises on security architecture
- **Senior SDE**: Reviews code for vulnerabilities; provides secure coding guidance
- **DevOps/SRE**: Partners on infrastructure security, secrets, incident response
- **QA Engineer**: Integrates security tests into CI/CD pipeline
- **Principal SDE**: Reviews architecture for security implications; threat modeling
