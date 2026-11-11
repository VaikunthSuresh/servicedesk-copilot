# DEV-001: Internal GenAI Platform Access and API Keys (synthetic analogue)

Owner: AI Platform Team | Applies to: engineers building GenAI features

## Who Can Get Access
- Engineers in an approved GenAI project. The project must be registered in the AI use-case register before keys are issued.
- Each project gets one API key per environment (dev, test, prod). Personal keys are not issued.

## Requesting an API Key
1. Raise an "AI Platform Access" request with the project ID from the AI use-case register.
2. The project lead approves the request.
3. The AI Platform Team issues the dev key within 2 business days. Test and prod keys additionally need a completed AI risk assessment.
4. Keys are stored in the team's secrets vault. Never put keys in source code, tickets, chat or email.

## Quotas and Errors
- Default dev quota: 200,000 tokens per day per project. A 429 error means the quota is used up; it resets at 00:00 UTC.
- Quota increases are requested by the project lead with the expected daily volume.
- A 401 error usually means an expired key: dev keys expire every 90 days.

## Data Rules
Only data classified Public or Internal may be sent to the platform in dev. Confidential data needs an approved prod setup with logging disabled for prompts.
