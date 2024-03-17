# ugoku-kun

## Description

This is a utility built on Cannon's [ccapi](https://asia.canon/en/campaign/developerresources/sdk#digital-camera) for srtucture-from-motion (SFM).

## Network Configuration

**Important**: Inappropriate settings can lead to connection issues.

Kill any "smart" features on your router that automatically adjusts configurations shch as the following:

- Don't mix authentication methods -> If in doubt, use WPA2-PSK (AES) only
- Don't mix 2.4/5GHz bands -> set a dedicated SSID for 2.4GHz
- Don't mix channel width (20MHz/40MHz) -> set to either 20MHz ONLY or 40MHz ONLY
- Use channels 1-11 only -> Auto channel selection is OK as long as 12/13 channels are disabled


## Workflow

1. user sets up camera
2. get auto settings
   - shutter speed
   - exposure
   - iso(can be auto)
3. feedback values to xlsx or something
4. user manually check settings, override if inappropriate via xlsx
5. manually set lens if necessary
6. turn table and take photo: xlsx
   - shutter
   - 5 degree
7. export log
   - auto settings
   - log


Think about errors(for overnight measurement)
