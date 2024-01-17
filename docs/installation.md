ADSBCOT's functionality provided by a command-line program called `adsbcot`.

There are several methods of installing ADSBCOT. They are listed below, in order of complexity.

# Debian, Ubuntu, Raspberry Pi

Install ADSBCOT, and prerequisite packages of [PyTAK](https://pytak.rtfd.io) & [AIRCOT](https://aircot.rtfd.io).

```sh linenums="1"
sudo apt update
wget https://github.com/ampledata/aircot/releases/latest/download/python3-aircot_latest_all.deb
sudo apt install -f ./python3-aircot_latest_all.deb
wget https://github.com/ampledata/pytak/releases/latest/download/python3-pytak_latest_all.deb
sudo apt install -f ./python3-pytak_latest_all.deb
wget https://github.com/ampledata/adsbcot/releases/latest/download/python3-adsbcot_latest_all.deb
sudo apt install -f ./python3-adsbcot_latest_all.deb
```

# Windows, Linux

Install from the Python Package Index (PyPI) [Advanced Users]::

```sh
python3 -m pip install adsbcot
```

# Developers

PRs welcome!

```sh linenums="1"
git clone https://github.com/snstac/adsbcot.git
cd adsbcot/
python3 setup.py install
```
