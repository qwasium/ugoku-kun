# ugoku-kun

This is a Python library for controlling Cannon cameras and Keigan Motor for SfM (Structure from Motion) applications.

This Python library is built as part of an internship project at the National Agriculture and Food Research Organization (NARO) in Japan.

## Documentation

Please refer to the documentation for more details.

[Documentation](https://ugoku-kun.readthedocs.io/en/latest/)

## Codemap

- `README.md`: This file.
- ugoku_kun: The main package.
  - `__init__.py`
  - `cannon_wrapper.py`: The camera module `CannonWrapper`.
  - `keigan_wrapper.py`: The Keigan Motor module `KeiganWrapper`.
  - `ugoku_kun.py`: The main module `UgokuKun`.
  - `ugoku_helers.py`: The utility module `UgokuHelpers`.
- docs/*: The documentation. WIP.
- tests/*: Tests, not automated, WIP.
- readme_demo: Read this for quick start.
  - `readme.ipynb`: READ THIS FIRST.

## Dependencies

This Python library is built on top of official APIs provided by Cannon and Keigan.

- Cannon's [ccapi](https://asia.canon/en/campaign/developerresources/sdk#digital-camera)
- Keigan's [pykeigan](https://github.com/keigan-motor/pykeigan_motor)

Tested on:

- Ubuntu 22.04
- Python 3.10.12
- Cannon EOS R100 firmware 1.6.0
- Keigan Motor KM-1S-M6829-TS
- pykeigan-motor 2.4.0 via pip

Should work on Windows too. ccapi is platform independent.
