# AppDaemon scripts for Home Assistant

## cast.py
When casting HA to a Google Cast device using CATT, there is a known issue that the casting stops after 10 minutes and needs to be somehow restarted. This script does just that. It monitors the status of casting and recasts if necessary.

This script requires [browser_mod](https://github.com/thomasloven/hass-browser_mod) to work.

Furthermore, `pythonping` needs to be installed in the AppDaemon's container. If logging to syslog is desired, `pysyslogclient` is also needed.

Example:

```
python_packages:
  - pysyslogclient
  - pythonping
```
