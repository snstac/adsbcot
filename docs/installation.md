ADSBCOT's functionality provided by a command-line program called `adsbcot`.

There are several methods of installing ADSBCOT. They are listed below, in order of complexity.

## Debian, Ubuntu, Raspberry Pi

Install ADSBCOT, and prerequisite packages of [PyTAK](https://pytak.rtfd.io) & [AIRCOT](https://aircot.rtfd.io).

```sh linenums="1"
sudo apt update -qq
wget https://github.com/snstac/aircot/releases/latest/download/aircot_latest_all.deb
sudo apt install -f ./aircot_latest_all.deb
wget https://github.com/snstac/pytak/releases/latest/download/pytak_latest_all.deb
sudo apt install -f ./pytak_latest_all.deb
wget https://github.com/snstac/adsbcot/releases/latest/download/adsbcot_latest_all.deb
sudo apt install -f ./adsbcot_latest_all.deb
```

> **N.B.** This installation method only supports `http://` & `file://` based ADS-B data feeds. To use TCP RAW (SBS-1) or TCP binary Beast protocols, you'll need to install pyModeS, see below.

## Windows, Linux

Install from the Python Package Index (PyPI) [Advanced Users]::

```sh
sudo python3 -m pip install adsbcot
```

## TCP BaseStation (SBS-1) & TCP binary Beast support

If you'd like to read decoded ADS-B data over the network, you must install ADSBCOT with the extra pymodes package:

```sh
sudo python3 -m pip install adsbcot[with_pymodes]
```

## ADSBExchange.com Raspberry Pi

These instructions are exclusively for systems running the ADSBExchange.com Raspberry Pi image.

```sh linenums="1"
sudo apt update
sudo apt install -y python3-pip
sudo python3 -m pip install adsbcot
```

## Docker

Build the docker container.

```sh linenums="1"
git clone https://github.com/snstac/adsbcot.git
cd adsbcot/
docker build -t adsbcot -f docker/Dockerfile .
```

Run the docker container with config folder mounted locally. Config files can be edited in the local folder ```/opt/docker/adsbcot/```.

```sh linenums="1"
docker run -d -v /opt/docker/adsbcot/:/etc/adsbcot --name adsbcot adsbcot
```

## Developers

PRs welcome!

```sh linenums="1"
git clone https://github.com/snstac/adsbcot.git
cd adsbcot/
python3 setup.py install
```
