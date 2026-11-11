# SOP-002: Password Reset and Account Lockout

Owner: Identity & Access Management | Applies to: Active Directory / Entra ID accounts

## Policy
- Passwords expire every 90 days and must be at least 14 characters.
- Accounts lock after 5 failed attempts in 15 minutes; lockout lasts 30 minutes.
- Service desk agents must verify identity (employee ID + manager name, or a callback to the registered mobile) before any reset. Never reset a password based on an email request alone.

## Self-Service Reset (preferred)
1. Direct the user to the Self-Service Password Reset portal.
2. The user verifies with MFA and sets a new password.
3. On Windows, the user locks and unlocks the laptop (Win+L) while on the corporate network or VPN to sync the cached credential.

## Agent-Assisted Reset
1. Verify identity as per policy.
2. In AD Users and Computers, right-click the account, choose "Reset Password", tick "User must change password at next logon".
3. If the account is locked, tick "Unlock account".
4. Log the verification method in the ticket. Never send the temporary password by email; share it by phone.

## Repeated Lockouts
Repeated lockouts within a day usually mean an old password is cached on a phone (Outlook/Teams mobile) or a mapped drive. Ask the user to update the password on all devices. If lockouts continue, escalate to IAM (L2) to check the lockout source in the domain controller logs.

## Security Note
If the user did not trigger the lockout themselves, treat it as a possible attack: priority P1, route to the Security Operations Centre (SOC).
