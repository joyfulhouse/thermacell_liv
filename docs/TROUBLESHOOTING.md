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

## Getting Help

If you are still stuck, open an issue at
<https://github.com/joyfulhouse/thermacell_liv/issues> with debug logs, a
diagnostics file, and reproduction steps.
