# DEV-002: Cloud Sandbox Accounts and CI/CD Pipeline Issues (synthetic analogue)

Owner: Cloud Platform Team

## Sandbox Accounts
- Each team gets one cloud sandbox account with a monthly budget (default equivalent of 1,000 USD).
- At 80% of budget the team lead gets an alert; at 100% new compute resources are blocked automatically.
- A budget increase is requested by the team lead with a cost centre; approval takes 1 business day.
- Sandboxes must not hold production or customer data.

## Pipeline Failures
1. Check the platform status page first: a known incident means the ticket is linked to it and no further troubleshooting is needed.
2. "No runner available" errors: shared runners are limited to 20 concurrent jobs per team; queue or cancel old jobs.
3. Pipelines failing with "quota exceeded" or "resource creation denied" in the sandbox usually mean the budget limit has been reached.
4. Credential errors in pipelines: rotate the service account secret in the vault; secrets expire every 90 days.

## Priority
A whole team blocked from deploying to the shared test environment is P2. A production deployment pipeline down is P1 and pages the Cloud Platform on-call engineer.
