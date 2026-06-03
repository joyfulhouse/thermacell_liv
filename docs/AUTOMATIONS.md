# Automation Examples

Realistic automations, scripts, and dashboard cards for Thermacell LIV. Replace
`patio` with your device name. For a couple of quick examples, see the
[README](../README.md#automation-examples).

## Use Cases

- **Home & patio** — enable the repeller at sunset for mosquito-free outdoor
  dining; schedule protection through peak mosquito hours.
- **Events & gatherings** — coordinate multiple hubs for large areas; monitor
  and control remotely while camping or hosting a BBQ.
- **Smart home** — auto-enable on outdoor motion or arrival, disable during
  rain, run from dusk to dawn.
- **Maintenance** — get low-refill notifications and track runtime to plan
  refills.

## Automations

### Patio protection at sunset (with conditions)

```yaml
automation:
  - alias: "Patio Protection - Start at Sunset"
    trigger:
      - platform: sun
        event: sunset
        offset: "-00:30:00"  # 30 minutes before sunset
    condition:
      - condition: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 60  # only when warm enough for mosquitoes
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 128
          rgb_color: [255, 200, 100]  # warm amber

  - alias: "Patio Protection - Stop at Midnight"
    trigger:
      - platform: time
        at: "00:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.thermacell_liv_patio
```

### Change LED color at a set time

```yaml
automation:
  - alias: "Thermacell LED Evening Color"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          rgb_color: [255, 100, 0]  # orange
          brightness: 128
```

### Low refill alert

```yaml
automation:
  - alias: "Thermacell - Low Refill Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.thermacell_liv_patio_refill_life
        below: 20  # alert at 20% remaining
    action:
      - service: notify.mobile_app
        data:
          title: "Thermacell Refill Low"
          message: >-
            Patio Thermacell refill at
            {{ states('sensor.thermacell_liv_patio_refill_life') }}%.
            Order a replacement soon.
          data:
            priority: high
```

### Presence-based protection

```yaml
automation:
  - alias: "Thermacell - Auto Start When Home"
    trigger:
      - platform: state
        entity_id: person.family_member
        to: "home"
    condition:
      - condition: sun
        after: sunset
        before: sunrise
      - condition: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 65
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - delay:
          seconds: 30  # wait for warming up
      - service: notify.mobile_app
        data:
          message: "Patio mosquito protection activated!"
```

### LED color by protection status

Drive the LED color from the system-status sensor as a visual indicator.

```yaml
automation:
  - alias: "Thermacell LED - Visual Status Indicator"
    trigger:
      - platform: state
        entity_id: sensor.thermacell_liv_patio_system_status
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Protected"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [0, 255, 0]  # green = protected
                  brightness: 255
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Warming Up"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [255, 165, 0]  # orange = warming
                  brightness: 200
          - conditions:
              - condition: state
                entity_id: sensor.thermacell_liv_patio_system_status
                state: "Error"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.thermacell_liv_patio_led
                data:
                  rgb_color: [255, 0, 0]  # red = error
                  brightness: 255
```

## Scripts

### Outdoor event mode

```yaml
script:
  thermacell_event_mode:
    alias: "Thermacell - Outdoor Event Mode"
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 200
          rgb_color: [255, 255, 255]  # bright white for visibility
      - service: notify.mobile_app
        data:
          message: "Outdoor event mode activated - mosquito protection on!"
```

### Night mode (dim LED)

```yaml
script:
  thermacell_night_mode:
    alias: "Thermacell - Night Mode"
    sequence:
      - service: switch.turn_on
        target:
          entity_id: switch.thermacell_liv_patio
      - service: light.turn_on
        target:
          entity_id: light.thermacell_liv_patio_led
        data:
          brightness: 50  # dim for nighttime
          rgb_color: [255, 50, 0]  # deep red (night-vision friendly)
```

## Dashboard Card

```yaml
type: entities
title: Patio Mosquito Protection
entities:
  - entity: switch.thermacell_liv_patio
    name: Protection
    icon: mdi:shield-bug
  - entity: sensor.thermacell_liv_patio_system_status
    name: Status
  - entity: sensor.thermacell_liv_patio_refill_life
    name: Refill Life
  - entity: sensor.thermacell_liv_patio_system_runtime
    name: Runtime
  - entity: light.thermacell_liv_patio_led
    name: LED Light
  - type: button
    name: Reset Refill
    action_name: Reset
    tap_action:
      action: call-service
      service: button.press
      service_data:
        entity_id: button.thermacell_liv_patio_reset_refill
```
