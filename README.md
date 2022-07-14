# AppDaemon scripts for Home Assistant

## cast.py
When casting HA to a Google Cast device using CATT, there is a known issue that the casting stops after 10 minutes and needs to be somehow restarted. This script does just that. It monitors the status of casting and recasts if necessary.
