# ugoku-kun

## Description

This is a utility built on Cannon's [ccapi](https://asia.canon/en/campaign/developerresources/sdk#digital-camera) for srtucture-from-motion (SFM).

Camera only connects with:

- 2.4GHz Wi-Fi
- WPA2-PSK (AES) / shared key / open

kill any "smart" features on your router that automatically adjusts configurations of:

- type of authentication
- 2.4GHz/5GHz bands
- channel width (20MHz/40MHz)

Set them manually such as: WPA-PSK (AES), 2.4GHz, 40MHz


1. user sets up camera
2. get auto settings
   - shutter speed
   - exposure
   - iso
3. feedback values to xlsx or something
4. user manually check settings, override if inappropriate via xlsx
5. manually set lens if necessary
6. turn table and take photo: xlsx
   - shutter
7. export log
   - auto settings
   - log

Think about errors(for overnight measurement)
