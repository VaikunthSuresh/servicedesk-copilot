# OPS-003: Platform Access, Availability and Ticket Priority (synthetic analogue)

Owner: Data Platform Operations

SYNTHETIC document written for a university assignment. Schedules and SLAs are invented.

## Access requests
- Workspace access and Unity Catalog permissions are granted to Azure AD (Entra ID) groups, never to individual users.
- Read access to a catalog schema needs approval from the **data owner** of that schema. A line manager's approval alone is not enough; requests without data-owner approval are sent back.
- Raise access as a ServiceNow **service request** (not an incident), naming the schema and the business need. Once approved, access is applied within 1 business day.
- Service principals for pipelines are requested by the pipeline owner, never by end users.

## Availability and maintenance window
- Planned maintenance: **Sundays 02:00-06:00 IST**. Scheduled ADF triggers and Databricks job schedules are **paused** during the window and resume afterwards.
- Unplanned outages are announced on the platform status page.

## ServiceNow priority matrix
| Priority | When |
|---|---|
| P1 - Critical | Production pipeline or job failure that leaves business reports or dashboards empty or wrong; platform unavailable for all users |
| P2 - High | Production failure with a workaround or rerun possible; a single team blocked |
| P3 - Normal | Non-production failures, performance issues, questions |
| P4 - Low | Service requests such as access requests |
