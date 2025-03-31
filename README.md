![ATAK screenshot with PyTAK logo.](https://adsbcot.readthedocs.io/en/latest/media/atak_screenshot_with_pytak_logo-x25.png)

# Display Aircraft in TAK - ADS-B feed to TAK Gateway 

ADSBCOT is software for monitoring and analyzing aviation surveillance data via the Team Awareness Kit (TAK) ecosystem of products.

For detailed documentation, visit the [official documentation](https://adsbcot.rtfd.io).

## Features

- Converts ADS-B messages to Cursor on Target (CoT) format.
- Retains aircraft track, course, speed vectors and other metadata.
- Compatible with TAK products: ATAK, TAKX, WinTAK, and iTAK.
- Supports multiple ADS-B data aggregators.
- Supports COTS ADS-B hardware receivers.
- Supports over-the-air RF ADS-B data via SDR.
- Runs on Python 3.7+ in both Windows and Linux environments.

### Supported ADS-B Aggregators

- [ADS-B Exchange](https://www.adsbexchange.com/)
- [adsb.fi](https://adsb.fi/)
- [ADS-B Hub](https://www.adsbhub.org/)
- [Airplanes.Live](https://airplanes.live/)

### Supported ADS-B Receivers

- [Piaware](https://www.flightaware.com/adsb/piaware/)
- [ADS-B Exchange](https://www.adsbexchange.com/ways-to-join-the-exchange/)
- [Stratux ADS-B](https://stratux.me/)
- Any SDR (RTL-SDR, HackRF, etc.)

### Supported ADS-B Decoders

- [readsb](https://github.com/wiedehopf/readsb)
- [dump1090](https://github.com/antirez/dump1090)
- [dump1090-fa](https://github.com/edgeofspace/dump1090-fa)
- [dump1090-mutability](https://github.com/adsb-related-code/dump1090-mutability)

## Related Projects

- [AirTAK](https://www.snstac.com/store/p/airtak-v1): A turn-key ADS-B to TAK Gateway solution.
- [WarDragon](https://cemaxecuter.com/?product=wardragon-pro-kit)
- StratuxCOT & ADSBXCOT functionality has been merged into ADSBCOT.

## Copyright & License

Copyright Sensors & Signals LLC https://www.snstac.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
