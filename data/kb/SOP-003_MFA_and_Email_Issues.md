# SOP-003: MFA Re-registration and Outlook/Email Issues

Owner: Collaboration Services

## MFA Re-registration (new or lost phone)
1. Verify identity (see SOP-002 policy).
2. In the Entra ID admin portal, open the user, select "Authentication methods", and choose "Require re-register MFA".
3. Ask the user to sign in at the MFA setup page from a laptop and scan the new QR code with Microsoft Authenticator.
4. Temporary Access Passes are valid for 8 hours and may only be issued by L2.

## Outlook Not Syncing / Disconnected
1. Check the service health dashboard for an active Exchange Online incident. If there is one, link the ticket to the master incident and do not troubleshoot further.
2. Ask the user to restart Outlook. If it still shows "Disconnected", start Outlook in safe mode (`outlook.exe /safe`) to rule out add-ins.
3. Recreate the Outlook profile from Control Panel > Mail > Show Profiles if safe mode works but normal mode does not.
4. If the mailbox is above 95% of quota, guide the user to archive mail older than 12 months.

## Suspected Phishing Email
Do not ask the user to forward the email. Ask them to use the "Report Phishing" button in Outlook. If the user clicked a link or entered credentials, reset their password immediately (SOP-002), revoke sessions in Entra ID, and route to SOC as P1.
