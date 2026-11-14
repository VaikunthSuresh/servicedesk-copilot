# OPS-001: Azure Data Factory (ADF) Pipeline Failure Runbook (synthetic analogue)

Owner: Data Platform Operations

SYNTHETIC document written for a university assignment. Not a real company runbook; pipeline names and times are invented.

## First checks for any failed pipeline
1. Open ADF Studio, go to **Monitor > Pipeline runs**, and open the failed run.
2. Note the failed activity, its error code and error message. Paste the error into the ServiceNow ticket.
3. Check whether other pipelines using the same linked service or integration runtime failed in the same window.

## Common failure causes and fixes
| Error or symptom | Likely cause | Fix |
|---|---|---|
| AADSTS7000222 "client secret keys are expired" | The service principal's client secret has expired | Create a new client secret for the service principal, update it in Azure Key Vault, confirm the linked service reads it, then rerun from the failed activity |
| "Path does not exist" / source file not found | Source file arrived late or under a different name | Confirm with the source team; rerun once the file is present |
| Integration runtime offline | Self-hosted IR machine stopped or lost connectivity | Restart the IR service; escalate to infrastructure if the machine is down |
| Activity timeout | Source slow or data volume grew | Rerun; if repeated, raise the activity timeout and review the query |
| Copy activity schema mismatch | Source added or renamed columns | Update the mapping or dataset schema, then rerun |

## Rerunning
- To rerun only what failed: **Monitor > Pipeline runs >** open the run **> Rerun from failed activity**. This skips the activities that already succeeded.
- Rerun the whole pipeline only if earlier activities need to run again (for example after a source correction).

## Escalation
If a production pipeline cannot be fixed within 2 hours, escalate to the platform lead and notify the owners of downstream reports.
