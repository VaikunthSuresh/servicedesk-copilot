# SOP-005: Corporate Wi-Fi and Office Network Access

Owner: Network Operations | Applies to: all office locations

## Networks
- **CORP-SECURE**: for company laptops only. Uses certificate-based authentication (EAP-TLS); no password is needed.
- **CORP-GUEST**: for visitors and personal phones. A daily voucher is issued by Reception and expires at midnight.
- Personal devices must never be connected to CORP-SECURE.

## Laptop Cannot Join CORP-SECURE
1. Confirm the laptop shows a valid device certificate (Windows: certlm.msc → Personal → Certificates; macOS: Keychain Access → System).
2. Certificates renew automatically every 12 months, but only while the laptop connects to the corporate network or VPN at least once every 30 days. A laptop that has been offline longer must be connected by Ethernet in the office to renew.
3. Forget the CORP-SECURE network and rejoin.
4. If several users on the same floor cannot connect, raise a P2 for Network Operations — likely an access point fault. Note the floor and the nearest meeting room name.

## Slow Wi-Fi in the Office
- Check whether the user is on CORP-GUEST by mistake; it is rate-limited to 5 Mbps per device.
- Ask the user to run the internal speed test page. Results under 20 Mbps on CORP-SECURE should be logged with the location for Network Operations.
