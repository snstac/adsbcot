Running
=======

In a terminal
-------------

ADSBCOT should run on most systems out of the box by logging into a terminal (ssh) and typing: ``adsbcot``

This will run ADSBCOT in the 'foreground' of your terminal. If you exit or disconnect 
from your terminal, ADSBCOT will also exit. 

To run ADSBCOT with a specific configuration file, you can type: ``adsbcot -c config.ini``, 
where ``config.ini`` is the name of your configuration file. For configuration options; see :doc:`config`.

As a background system service
------------------------------

To keep ADSBCOT running in the background, it is recommended to run it as a system service ("daemon") using systemd. 
This example assumes ADSBCOT was installed with ``pip`` and its executable is located at ``/usr/local/bin/adsbcot``. 
If your system differs, you'll need to change the following code-block to match the installation location for the 
``adsbcot`` executable and, if applicable, the configuration file. (Try: ``find / -name adsbcot -type f``)

1. Copy the following code block to ``/etc/systemd/system/adsbcot.service``::

    [Unit]
    Description=ADS-B to TAK Gateway
    After=network.target
    [Service]
    ExecStart=/usr/local/bin/adsbcot -c /etc/adsbcot.ini
    Restart=always
    RestartSec=5
    [Install]
    WantedBy=network.target

(You can create ``adsbcot.service`` using Nano: ``$ sudo nano /etc/systemd/system/adsbcot.service``)

2. Create the ``/etc/adsbcot.ini`` file and add an appropriate configuration (See also: :doc:`config`)::
    
    $ sudo nano /etc/adsbcot.ini

3. Enable cotproxy systemd service::
    
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable adsbcot
    $ sudo systemctl start adsbcot

4. You can view logs with: ``$ sudo journalctl -fu adsbcot``
