
To report bugs, please set the DEBUG=1 environment variable to collect logs:

```sh
DEBUG=1 adsbcot
```

Or:

```sh linenums="1"
export DEBUG=1
adsbcot
```

Or:

```sh linenums="1"
echo 'DEBUG=1' >> adsbcot.ini
adsbcot -c adsbcot.ini
```

You can view systemd/systemctl/service logs via:

```journalctl -fu adsbcot```

Please use GitHub issues for support requests. Please note that ADSBCOT is free open source software and comes with no warranty. See LICENSE.