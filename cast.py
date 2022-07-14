import hassapi as hass
import subprocess
from pythonping import ping

try:
    import pysyslogclient
    from pysyslogclient import SEV_DEBUG, SEV_WARNING, SEV_ERROR, SEV_CRITICAL, SEV_NOTICE
except:
    SEV_DEBUG = SEV_WARNING = SEV_ERROR = SEV_CRITICAL = SEV_NOTICE = None

class Cast(hass.Hass):

    USE_SYSLOG = False # Change to True for syslog logging (requires a remote syslog server)
    
    SYSLOG_MY_NAME = "AppDaemon.Cast"
    SYSLOG_SERVER = "192.168.1.x" # Put your syslog server's IP address here (required if USE_SYSLOG is True)
    SYSLOG_PORT = 514

    ENTITY = "sensor.browser_catt" # Put your display's browser entity here (provided by browser_mod)
    CAST_IP = "192.168.1.x" # Put your display's IP address here
    CAST_SITE_URL = "http://192.168.1.x:8123/" # Put your HA's URL here
    
    def logr(self, msg, severity=None):
        try:
            self.syslog.log("- " + str(msg), hostname=Cast.SYSLOG_MY_NAME, severity=severity)
        except:
            self.log(str(msg))

    def initialize(self):
        if Cast.USE_SYSLOG:
            self.logr("Logging to syslog")
            self.syslog = pysyslogclient.SyslogClientRFC5424(Cast.SYSLOG_SERVER, Cast.SYSLOG_PORT, proto="UDP")
        
        self.logr("Init", severity=SEV_NOTICE)

        self.entity = self.get_entity(Cast.ENTITY)
        self.register_listener()
        self.cast_if_needed()
        
    def register_listener(self):
        self.logr("Registering state listener", severity=SEV_DEBUG)
        self.disable_listener()
        self.listener = self.entity.listen_state(self.on_state_change, attribute="all")
        
    def enable_listener(self):
        self.logr("Enabling listener", severity=SEV_DEBUG)
        self.listener = True
    
    def disable_listener(self):
        self.logr("Disabling listener", severity=SEV_DEBUG)
        self.listener = False

    def on_state_change(self, entity, attr, old, new, kwargs):
        state_old, visibility_old, width_old = old["state"], old["attributes"].get("visibility"), old["attributes"].get("width")
        state_new, visibility_new, width_new = new["state"], new["attributes"].get("visibility"), new["attributes"].get("width")
        
        if state_old == state_new and visibility_old == visibility_new and width_old == width_new:
            return
        
        if not self.listener:
            self.logr("Ignoring state change", severity=SEV_DEBUG)
            return
        
        self.disable_listener()
        self.logr(f"State change trigger: old = {state_old}/{visibility_old}/{width_old}, new = {state_new}/{visibility_new}/{width_new}", severity=SEV_DEBUG)
        self.cast_if_needed()
    
    def on_timer_expired(self, kwargs):
        self.logr("Timer expired trigger", severity=SEV_DEBUG)
        self.cast_if_needed()
            
    def get_state(self):
        state = self.entity.get_state(attribute="all")
        
        try:
            state["state"] = int(state["state"])
        except:
            pass
        
        return state
    
    def cast_if_needed(self):
        state = self.get_state()
        state_value = state["state"]
        visibility = state["attributes"].get("visibility")
        width = state["attributes"].get("width")
        
        if state_value != 1 or visibility != "visible" or width != 1024:
            self.logr(f"Current state = {state_value}, visibility = {visibility}, width = {width}")
            self.cast()
        else:
            self.logr(f"Current state = {state_value}, visibility = {visibility}, width = {width}", severity=SEV_DEBUG)
            self.logr("Already casting", severity=SEV_DEBUG)
            self.enable_listener()
    
    def catt(self, *params):
        command = ["timeout", "30", "catt", "-d", Cast.CAST_IP] + list(params)
        self.logr("Issuing command: " + " ".join(command), severity=SEV_DEBUG)
        res = subprocess.run(command, check=True)
    
    def cast(self):
        try:
            self.logr("Attempting to cast")

            ping(Cast.CAST_IP)
            
            self.catt("volume", "0")
            self.catt("stop")
            self.catt("cast_site", Cast.CAST_SITE_URL)
            self.catt("volume", "50")
        except Exception as e:
            self.logr("Exception: " + str(e), severity=SEV_ERROR)
            
        finally:
            self.run_in(self.on_timer_expired, 15)
