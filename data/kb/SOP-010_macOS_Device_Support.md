# SOP-010: macOS Device Support

Owner: End User Computing (EUC) — Mac team

## VPN on macOS
- The supported client on macOS is GlobalProtect 6.2 or later from Self Service.
- After a macOS major upgrade, approve the GlobalProtect system extension: System Settings → Privacy & Security → "Allow" for Palo Alto Networks. Without this the VPN connects but no traffic passes.
- If it still fails, remove GlobalProtect with the uninstaller in Self Service and reinstall.

## FileVault Recovery Key
Macs are encrypted with FileVault. If a Mac asks for the FileVault recovery key, retrieve it from the device management console (Jamf) after verifying identity as per SOP-002. Never send the key by email or chat; read it out over a call.

## Software and Updates
- Software is installed from Self Service (see SOP-007).
- macOS updates are deferred 14 days after release and then enforced; users get 3 deferrals before a forced restart.

## Slow Mac
Check Activity Monitor for high memory pressure (yellow or red). Spotlight indexing after an upgrade can slow a Mac for up to 24 hours; this is expected.
