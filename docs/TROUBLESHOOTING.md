# Troubleshooting

Common problems with Thermacell LIV and how to resolve them. For a short
summary, see the [README](../README.md#troubleshooting).

## Common Issues

### Authentication failed

- Verify the username/password work in the Thermacell mobile app.
- Ensure the account is active and the email is verified.
- Confirm devices are registered in the app.
- Use the reauthentication flow (**Settings → Devices & Services → Thermacell
  LIV → Reconfigure**).
- If it persists, reset the password on the Thermacell website, then reauth.

### No devices found

- Ensure the hubs are powered on and the LED is lit.
- Confirm they are online in the mobile app and on a 2.4 GHz network.
- Press the diagnostic refresh button, or reload the integration (**⋮ →
  Reload**).
- If it persists, remove and re-add the integration.

### Connection timeout

- Test internet connectivity from Home Assistant.
- Confirm the API URL `https://api.iot.thermacell.com/` is reachable and not
  blocked by an outbound firewall.
- Review Home Assistant logs for the detailed error, and check the Thermacell
  API status.

### LED not responding

- Verify the hub is powered on (LED lit) and online (connectivity sensor).
- Test control from the mobile app to rule out a hardware issue.
- Ensure brightness is greater than 0 — the LED is off at brightness 0.

### LAN unavailable or cloud fallback

- Confirm local preference is enabled and the hub advertises local-control
  capability in authenticated account metadata. Firmware without that service
  cannot use this path; see
  [live hub status (2026-10-18)](NATIVE_CONTROLS.md#live-hub-status-2026-10-18)
  for the measured capability limits. The diagnostic command is available from
  pythermacell PR #73 / the next pythermacell release, not in the pinned 0.3.0b3.
- Check `_esp_local_ctrl._tcp.local.` mDNS visibility **from Home Assistant's
  network/interface**. A short negative browse is inconclusive. Across VLANs,
  verify multicast reflection as well as routed TCP access to the advertised port;
  discovery visibility does not establish endpoint reachability.
- Check all advertised address families/routes. The integration prefers IPv4,
  then non-link-local IPv6, then link-local addresses (IPv6 needs a scope).
  Read failures try bounded alternatives then cloud. Writes do not retry across
  addresses or replay through cloud; refresh before manually retrying an uncertain
  command.
- A discovered endpoint is not proof of authenticated pairing or a successful
  read. Security/PoP/username come from cloud account metadata, never TXT records.
  Do not weaken security or publish those values while diagnosing handshakes.
- Late account/capability metadata is re-evaluated after coordinator refreshes.
  Timed-out announcements get at most three resolution attempts per announcement;
  a later mDNS update resets that budget. Removed aliases keep a transport only
  while another valid alias owns it; account removal prunes local control.
- The transport sensor is a library route hint, not a success or per-refresh
  measurement. `cloud` can describe an attempted fallback; `local` can coexist
  with cloud config/status. See [operation boundaries](NATIVE_CONTROLS.md#operation-boundaries).
- Setup and restart require cloud login. During a runtime outage only previously
  paired, discovered, local-capable hubs with cached metadata may continue;
  authentication failures (401/403) do not take the cached server-error path.
  Offline restart is **UNSUPPORTED**. OTA, groups, and account membership remain
  cloud-only. Avoid reload during an outage: it discards ephemeral local state.

### Slow response times

- Check internet speed and latency; increase the scan interval if the API is
  slow.
- Verify you are not hitting rate limits (see the logs). Optimistic updates
  still give instant UI feedback for your own actions.

### Entities unavailable

- Check the connectivity sensor and the device's status in the mobile app.
- Review logs for API errors; try a manual refresh or reload.
- Confirm credentials have not expired (reauth if needed).

## Enabling Debug Logging

```yaml
logger:
  default: info
  logs:
    custom_components.thermacell_liv: debug
    custom_components.thermacell_liv.coordinator: debug
```

This logs API requests/responses, authentication attempts, node online/offline
transitions, service-call outcomes, and optimistic-update operations.

## Diagnostics

1. **Settings → Devices & Services → Thermacell LIV**.
2. **⋮ → Download Diagnostics**.
3. Attach the file when reporting an issue (sensitive data is auto-redacted).

Diagnostics use anonymous node/device labels and allowlisted support fields,
including firmware/model, LED state, maintenance history, command audit, reported
power, and refill-drain evidence. Account titles/IDs and local credentials are
omitted or redacted by key, including sensitive fields nested in support data.
Free-form message fields are redacted because they can embed credentials.
Review debug logs separately before sharing them; diagnostics redaction does not
sanitize log files.

### If you shared a secret

Inspect exports and logs before posting. If a secret was uploaded, promptly
remove the upload; deleting it does not revoke copies already obtained. Change
the Thermacell cloud password and reauthenticate the integration. Existing cloud
sessions/tokens may remain valid for their remaining lifetime; do not assume
immediate revocation.

PoP and local username are vendor-provisioned and not user-rotatable. A cloud
password change does **not** rotate PoP. Disable local preference and reload the
integration, and treat the network segment as exposed until it is isolated or
the vendor reprovisions local credentials. The integration does not persist PoP.
There is no automated leak detection or credential revocation, and no measured
revocation time is provided.

## Getting Help

If you are still stuck, open an issue at
<https://github.com/joyfulhouse/thermacell_liv/issues> with debug logs, a
diagnostics file, and reproduction steps.
