# Windows Setup Note: ST-Link/V3 `hla_swd` Transport Fix

## Symptom
Running `pio run -e stm32 -t upload` on Windows with the WioE5 board fails immediately with:

```
Debug adapter doesn't support 'hla_swd' transport
*** [upload] Error 1
```

The build itself succeeds — this only happens at the upload/flash step.

## Cause
The onboard debug probe on the WioE5 dev board is an ST-Link/V3-class device
(identifiable via Device Manager or `pio device list` by VID:PID `0483:374F`).
**ST-Link/V3 probes dropped support for OpenOCD's legacy "HLA" (High Level**
**Adapter) transport mode, which is what the `hla_swd` transport selects.**

`platform-ststm32`'s `platform.py` hardcodes `hla_swd` for any board using
`upload_protocol = stlink`:

```python
"-c", "transport select %s" % (
    "hla_swd" if link == "stlink" else "swd"),
```

Anyone flashing this board from Windows with the onboard probe will hit this.
It's not project-specific or user-specific — it's a mismatch between the
platform package and this generation of ST-Link hardware.

## Workaround (confirmed working)
Edit the locally installed platform file:

```
C:\Users\<username>\.platformio\platforms\ststm32\platform.py
```

Change:

```python
"hla_swd" if link == "stlink" else "swd"),
```

to:

```python
"dapdirect_swd" if link == "stlink" else "swd"),
```

Save, then re-run the upload command. This is a **local, per-machine patch**
— it lives inside PlatformIO's package cache, not in this repo, so it needs
to be reapplied if the `ststm32` platform package is ever reinstalled or
updated (e.g. via `pio pkg update`).

## Note toward a permanent fix
OpenOCD itself flags `dapdirect_swd` as deprecated during the upload:

```
Warn : DEPRECATED! use 'transport select swd', not 'transport select dapdirect_swd'
```

This suggests recent OpenOCD versions have unified the old `hla_swd` /
`dapdirect_swd` split into a single `swd` transport that auto-detects the
connected probe's capability. If that holds up under testing, the real fix
belongs upstream in `platform-ststm32`: simplify the line to always select
`swd` regardless of `link`, removing the `hla_swd` special case entirely.
Worth testing against both an ST-Link/V2 and this V3 probe before submitting
as a small PR to `jlab-sensing/platform-ststm32`, so future users don't need
to hand-patch their local install at all.