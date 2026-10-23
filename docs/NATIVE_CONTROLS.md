# Native Controls and Refill Diagnostics

Available since **2.1.0**, with `pythermacell==0.3.1`. Contracts were
researched in Thermacell LIV Android 4.0.5 (versionCode 202). Timers and
verified power control are validated on live hubs; all paths have automated
HTTP/protocol and Home Assistant tests; see
[live hub status](#live-hub-status) for measured capability
limits. Firmware capabilities determine which controls appear.

| Capability | Home Assistant control |
|---|---|
| Run with automatic shutdown | Run for 30/60/120 minutes buttons |
| Custom duration | `thermacell_liv.run_for` action, 1-1440 minutes |
| Shutdown at a specific time | `thermacell_liv.schedule_shutdown`, within 24 hours |
| Cancel integration timer | Cancel shutdown timer button/action |
| App schedules and timers | Switch per schedule, with triggers/actions as attributes |
| Firmware | Check firmware updates button and update entity after a successful check |
| Maintenance | Reboot button when advertised by the hub |
| Hub timezone | IANA timezone text entity when writable |
| App groups | One power switch per Thermacell account group |
| LAN control (experimental) | Opt-in RainMaker mDNS discovery when supported; off by default |

## Timers and Schedules

```yaml
action: thermacell_liv.run_for
target:
  entity_id: switch.thermacell_liv_yard
data:
  minutes: 90
```

Target the main hub power switch or its device. Schedule/group switches are
excluded from these actions. The integration programs and enables a native
shutdown timer before starting power. If programming fails, power is not started.
If power verification fails, the programmed shutdown safeguard is retained.

`schedule_shutdown` takes `at`, a date/time. A value without a UTC offset uses
Home Assistant's local timezone. This action does not turn the hub on.
The deadline is converted to a native countdown, independent of the hub's
timezone. Execution is delegated to the hub even if HA subsequently stops;
firmware execution and operational shutdown still need confirmation.

The integration uses one timer per hub, ID `HA01`. Setting another duration
replaces that timer. Cancellation removes only that timer, leaving app schedules
and current power intact before its deadline. A timer's scheduled-shutdown sensor
is shown while enabled and remains visible after expiry until Off is confirmed.
The stored deadline is an estimate
from command acceptance; an app edit can change the hub's execution time.

At the first normal poll after an integration-owned deadline, HA checks fresh
parameters even if the native timer has disabled itself. Off requires a false
writable flag and explicit operational codes of 1, with no contradictory code.
If necessary, HA makes one verified off attempt with a 30-second timeout. The
attempt is remembered across reloads/restarts; it is not repeated each poll.
If shutdown remains unconfirmed, a persistent repair and the power-mismatch
diagnostic alert, and starts, replacement timers, and timer cancellation are
blocked until a fresh report confirms Off. The timer is retained. Explicit off
remains available. After manual recovery, refresh the integration to clear the
failure. Use HA's cancel action before the deadline to cancel the stop request;
disabling its schedule externally does not cancel HA's remembered deadline.

This is a mitigation for [issue #30](https://github.com/joyfulhouse/thermacell_liv/issues/30),
not a firmware fix. Firmware 5.4.7 on ADU has reported the enable flag false while
both operational codes remained Warming after native expiry and direct off.
Later identical tests passed without code or writable-settings changes. Cloud
reports cannot distinguish stale firmware/cloud reporting from physical heater
operation. The monitor requires HA and cloud connectivity and can run up to one
configured polling interval late; it cannot guarantee shutdown during an outage.
No automatic reboot, power-on recovery cycle, or refill reset is performed.
On 2026-10-23 the native 20-second expiry regression passed 3/3 repetitions on
each of two firmware 5.4.7 hubs with pythermacell 0.3.1, so the failure is
intermittent; it remains a documented known limitation. Per-repeller status and
temperature reports can also stay frozen at their last heating values until
the next activity, so treat them as last-reported values rather than live state.

Existing app schedules can be inspected and enabled/disabled. Schedule creation,
editing of recurring triggers, provisioning, sharing, and account management
remain in the app. Individual repeller control is not advertised by the observed
LIV API. Unsupported controls are omitted instead of probing parameter names.

## Firmware, Groups, and LAN

Firmware checks run every six hours, with a manual check button. Active OTA jobs
are polled at the normal integration interval and remembered across restarts.
The update entity shows the server's stage and details. No percentage is invented.
Installation rechecks the offered job and never accepts an arbitrary image URL.

Groups are refreshed every 15 minutes. Group power controls verify each known
member concurrently and report failed/offline members. Successful members keep
their resulting state when another member fails. Group switches are scoped to
the account entry, so names/IDs from multiple accounts do not collide.

The **Prefer local network control when supported (experimental)** option
defaults off; enable it in the integration options. Discovery
uses `_esp_local_ctrl._tcp.local.` and matches the advertised node ID to your
authenticated account. Credentials come from the hub's local-control service.
The transport supports the advertised Espressif security scheme without trying
weaker schemes. The local node identity is checked before writes. Only hubs that
advertise the service and are reachable through mDNS can use it.

Read failures can fall back to cloud. An attempted local write is not replayed
through cloud after a timeout, because it might already have reached the hub.
Refresh state before retrying. Power, LED, refill, native schedules, reboot and
timezone can use LAN; OTA and groups remain cloud operations. Read address
selection prefers usable IPv4, then non-link-local IPv6, then scoped link-local
IPv6. A failed local read can try other advertised addresses (at most eight);
a write uses exactly one endpoint, without address retry or cloud replay.

The connection-transport sensor is a **library route hint**, not proof of a
successful operation or a wholly local refresh. The library can mark `cloud`
before fallback succeeds, and a refresh may combine local params with cloud
config/status. Writes share the hint; it has no success timestamp. Before any
hint exists the sensor is unknown. Attributes explicitly say `proves_success:
false` and `per_refresh: false`; `local_endpoint_configured` means configuration,
not successful pairing/handshake. Per-operation successful read/write telemetry
requires a coordinated library follow-up.

Disable local preference and reload for cloud-only control; re-enabling also
reloads and requires cloud authentication. Discovery removal clears an endpoint,
and pruning its transport also clears the previous route hint.

### Operation boundaries

- **Setup:** cloud required for authentication, account enrollment, and trusted
  local security/credential metadata. mDNS never enrolls a foreign account node.
- **Runtime cloud outage:** conditional LAN operation for already-paired,
  discovered, local-control-advertising hubs with cached account metadata and a
  reachable authenticated endpoint. Cached-node fallback supports connection
  failures and some server errors. A 401/403 triggers reauthentication; a
  rejected reauthentication always surfaces as an authentication failure and
  never falls back to cached membership. A returned 401/403 after successful
  reauthentication does not qualify either. This is not a guarantee for every cloud error or firmware. See
  [live hub status](#live-hub-status).
- **Offline restart: UNSUPPORTED.** Startup/reload authenticates and refreshes
  through cloud before discovery, even for previously used hubs. No local
  bootstrap credentials/catalog are persisted by this integration.
- **Cloud-only features:** OTA offers/status/install, groups and their current
  membership, account membership/enrollment and credential provisioning/rotation.

Follow-up: [secure offline bootstrap](https://github.com/joyfulhouse/pythermacell/issues/76)
coordinates the library and HA: a versioned,
account-scoped catalog of previously paired nodes; protected PoP/local-username
storage and backup policy; identity/security verification after rediscovery;
credential revocation/rotation and membership reconciliation on cloud recovery;
and restart tests denying cloud while rejecting spoofed/unpaired nodes. HA
Store/config-entry persistence alone is not encryption. This design is deferred,
not an offline-startup feature in this phase.

### Live hub status

Checked 2026-10-18 UTC with the
[pythermacell LAN diagnostic](https://github.com/joyfulhouse/pythermacell/pull/73)
against two LIV hubs on firmware **5.4.7**. Neither hub advertised
`esp.service.local_control` in its account metadata: no security scheme, PoP, or
local username was provisioned. No `_esp_local_ctrl._tcp.local.` service was seen
from a homelab host (server0) that had mDNS multicast visibility of other LAN
services; hub VLAN co-location was not independently established.

No local handshake, local read, or local LED write was performed. On these hubs
the integration operates over cloud and the transport sensor will not show
`local`. A process-scoped cloud-denial run confirmed cloud connections were
blocked, but could not demonstrate LAN operation because there was no endpoint.

LAN control remains implemented and simulator-tested, but is unverified on
physical hubs; it requires firmware/provisioning that advertises local control.
If the sensor never shows `local`, first check whether the hub advertises local
control before investigating mDNS/VLAN. The `python -m pythermacell.diagnostics`
command is included in the pinned **0.3.1**. See the linked diagnostic for usage.

A subsequent UniFi investigation and direct-segment probes found eleven unnamed
Espressif candidates answering ping and refusing TCP 80/443/8080, with no local
RainMaker mDNS advertisements. Neither ADU nor Pool was conclusively mapped to
a client. This was not an exhaustive port scan or verified exhaustive candidate
set; no local connectivity was achieved, but per-hub port availability remains
inconclusive. No LED restoration is claimed because no live writes occurred.

## Refill State and Shutdown Evidence

- Refill type for next reset remains a preference. Changing it does not reset
  anything or claim a new cartridge is installed.
- A successful reset stores its time and applied type (40/100/180 hours).
  Estimated operating hours remaining use that capacity and the reported percent.
  They are not a predicted calendar depletion time.
- Unknown readings stay unknown. The app's `-1` sentinel raises Missing cartridge;
  zero percent remains a valid, present but empty cartridge. Low refill is <=10%.
- A missing cartridge or observed unexpected refill increase invalidates the
  capacity estimate because an app reset may have applied another type. Changes
  made entirely while HA is offline cannot be detected reliably; reset through
  HA to re-establish the applied type.
- Last command result includes the command, timestamp, requested power, and
  reported power. `confirmed` power means the library observed matching status;
  `accepted` on other commands means an API acknowledgement. Failed/cancelled
  commands do not prove the device remained unchanged.
- Requested-versus-reported power is a diagnostic comparison. App changes can
  legitimately make it differ. An unconfirmed timed shutdown also sets this
  diagnostic, independently of the last requested on command.
- Refill drain while off requires continuous online reports of Off plus a false
  writable power flag. After a two-minute settling period, a drop of at least
  two percentage points must persist across two samples, with at least ten
  minutes in the off window. Offline/unknown data and long polling gaps break
  the observation. This is evidence for investigation, not proof of physical use.

Use the diagnostic binary sensors as automation triggers for notifications.
The integration exposes the evidence without repeatedly resetting counters or
issuing automatic power commands in response to a suspected anomaly.

Protocol evidence and wire contracts:
[pythermacell native services](https://github.com/joyfulhouse/pythermacell/blob/main/docs/api/NATIVE_SERVICES.md).
