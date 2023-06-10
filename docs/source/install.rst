Installation
============

Functionality is provided by a command-line tool called ``adsbcot``, which can 
be installed either from the Python Package Index, or directly from source.


Most Users
----------

**Most Users**: Install ADSBCOT with file:// & http:// support ONLY.

If you're planning to run ADSBCOT on the same system running dump1090, you should 
install ADSBCOT from the Python Package Index (PyPI)::

    $ sudo python3 -m pip install adsbcot

**Other**: Install ADSBCOT with TCP Beast & TCP Raw support.

If you'd like to read decoded ADS-B data over the network, you must install ADSBCOT 
with the extra `pymodes` package::

    $ sudo python3 -m pip install adsbcot[with_pymodes]

**Alternate / Developers** 

Install ADSBCOT from the release zip file::

    $ wget https://github.com ...
    $ unzip ..
    $ cd adsbcot/
    $ python3 -m pip install

Install ADSBCOT from the GitHub hosted source repository::

    $ git clone https://github.com/snstac/adsbcot.git
    $ cd adsbcot/
    $ python3 -m pip install .


ADSBExchange.com Raspberry Pi image ONLY
----------------------------------------

These instructions are exclusively for systems running the ADSBExchange.com 
Raspberry Pi image::

    $ sudo apt update
    $ sudo apt install -y python3-pip
    $ sudo python3 -m pip install adsbcot
