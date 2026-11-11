# SOP-001: VPN Connectivity Troubleshooting (GlobalProtect / Cisco AnyConnect)

Owner: Network Operations | Applies to: all corporate laptops | Review cycle: quarterly

## Symptoms
- VPN disconnects every few minutes, or after an OS/client update.
- "Gateway not responding" or "Authentication failed" errors.
- Connected, but internal sites (intranet, Jira, SAP) do not load.

## L1 Resolution Steps
1. Confirm the user's internet works without VPN (open a public site). If not, follow SOP-004 Network Basics.
2. Ask the user to sign out of the VPN client, quit it fully from the system tray, and reconnect.
3. Check the client version. Supported: GlobalProtect 6.2 or later. Older clients must be updated from the Software Center.
4. If disconnects started after a Windows update, restart the "PanGPS" service (GlobalProtect) or "Cisco AnyConnect Secure Mobility Agent" service from services.msc.
5. Switch the gateway to the nearest region (Chennai, Hyderabad, Munich) in the client settings.
6. Flush DNS: run `ipconfig /flushdns` in an elevated Command Prompt, then reconnect.
7. If the user is on home Wi-Fi, ask them to disable "IPv6" on the Wi-Fi adapter as a temporary workaround.

## Authentication Failures
- Ensure the user's password has not expired (see SOP-002 Password Reset).
- MFA prompts must be approved within 60 seconds. If the user changed phones, re-register MFA via SOP-003.

## Escalation
Escalate to Network Operations (L2) with priority P2 if steps 1–7 fail, or P1 if more than 10 users at one site report the same issue (possible gateway outage). Attach the client log from `%ProgramData%\Palo Alto Networks\GlobalProtect\` to the ticket.
