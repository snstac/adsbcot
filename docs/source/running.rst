Running
=======

ADSBCOT should be started as a background sevice (daemon). Most modern systems 
use systemd.


Debian, Ubuntu, RaspberryOS, Raspbian
-------------------------------------

1. Copy the following code block to ``/etc/systemd/system/adsbcot.service``::

    [Unit]
    Description=ADS-B to TAK Gateway
    After=network.target
    [Service]
    ExecStart=/usr/bin/adsbcot -c /etc/adsbcot.ini
    Restart=always
    RestartSec=5
    [Install]
    WantedBy=network.target

(You can create ``adsbcot.service`` using Nano: ``$ sudo nano /etc/systemd/system/adsbcot.service``)

2. Create the ``/etc/adsbcot.ini`` file and add an appropriate configuration, see `Configuration <#Configuration>`_ section of the README::
    
    $ sudo nano /etc/adsbcot.ini

3. Enable cotproxy systemd service::
    
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable adsbcot
    $ sudo systemctl start adsbcot

4. You can view logs with: ``$ sudo journalctl -fu adsbcot``
