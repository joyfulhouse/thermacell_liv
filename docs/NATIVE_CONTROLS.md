# Native Controls and Refill Diagnostics

Available in **2.1.0-beta.1**, with `pythermacell==0.3.0b1`. Contracts were
researched in Thermacell LIV Android 4.0.5 (versionCode 202). This beta has
automated HTTP/protocol and Home Assistant tests; physical hub validation is
still outstanding. Firmware capabilities determine which controls appear.

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
| LAN control | Automatic RainMaker mDNS discovery when supported; option to disable |

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
timezone. The hub executes it even if HA subsequently stops.

The integration uses one timer per hub, ID `HA01`. Setting another duration
replaces that timer. Cancellation removes only that timer, leaving app schedules
and current power intact. A timer's scheduled-shutdown sensor is shown only when
the hub reports the matching timer enabled. The stored deadline is an estimate
from command acceptance; an app edit can change the hub's execution time.

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

The **Prefer local network control when supported** option defaults on. Discovery
uses `_esp_local_ctrl._tcp.local.` and matches the advertised node ID to your
authenticated account. Credentials come from the hub's local-control service.
The transport supports the advertised Espressif security scheme without trying
weaker schemes. The local node identity is checked before writes. Only hubs that
advertise the service and are reachable through mDNS can use it.

Read failures can fall back to cloud. An attempted local write is not replayed
through cloud after a timeout, because it might already have reached the hub.
Refresh state before retrying. Power, LED, refill, native schedules, reboot and
timezone can use LAN; OTA and group discovery remain cloud operations. Initial
setup/authentication still requires the cloud. Already-discovered local hubs can
continue during subsequent cloud outages. The connection-transport sensor shows
the most recently successful route. Disable the local preference and reload to
use cloud-only control if your network does not support the protocol.

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
  legitimately make it differ; the integration does not enforce an old request.
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
