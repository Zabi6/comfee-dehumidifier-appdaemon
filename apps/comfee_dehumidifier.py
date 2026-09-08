import subprocess
import sys
import hassapi as hass


class ComfeeDehumidifier(hass.Hass):
    def initialize(self):
        self.device_id = str(self.args["device_id"])
        self.account = self.args["account"]
        self.password = self.args["password"]
        interval = int(self.args.get("poll_interval", 300))
        self.power_entity = self.args.get("power_entity")
        self.target_entity = self.args.get("target_humidity_entity")
        self.fan_entity = self.args.get("fan_entity")
        self.mode_entity = self.args.get("mode_entity")

        self.run_every(self.poll, "now", interval)

        if self.power_entity:
            self.listen_state(self.on_power_change, self.power_entity)
        if self.target_entity:
            self.listen_state(self.on_target_change, self.target_entity)
        if self.fan_entity:
            self.listen_state(self.on_fan_change, self.fan_entity)
        if self.mode_entity:
            self.listen_state(self.on_mode_change, self.mode_entity)

    def _run_cli(self, extra_args):
        cmd = ["midea-beautiful-air-cli", "--log", "ERROR"] + extra_args + [
            "--id", self.device_id,
            "--account", self.account,
            "--password", self.password,
            "--cloud",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.log(f"CLI stdout: {result.stdout}")
            if result.returncode != 0:
                self.log(f"CLI stderr: {result.stderr}", level="WARNING")
            return result.stdout
        except Exception as e:
            self.error(f"Comfee CLI Fehler: {e}")
            return ""

    def poll(self, kwargs):
        output = self._run_cli(["status"])
        if not output:
            return
        data = {}
        for line in output.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()

        if "humid%" in data:
            self.set_state("sensor.comfee_luefter_luftfeuchte", state=data["humid%"],
                            attributes={"unit_of_measurement": "%", "friendly_name": "Comfee Lüfter Luftfeuchte"})
        if "target%" in data:
            self.set_state("sensor.comfee_luefter_zielfeuchte_ist", state=data["target%"],
                            attributes={"unit_of_measurement": "%", "friendly_name": "Comfee Lüfter Zielfeuchte (Gerät)"})
        if "tank" in data:
            self.set_state("binary_sensor.comfee_luefter_tank_voll",
                            state="on" if data["tank"] == "True" else "off",
                            attributes={"friendly_name": "Comfee Lüfter Tank voll"})
        if "running" in data:
            self.set_state("binary_sensor.comfee_luefter_laeuft",
                            state="on" if data["running"] == "True" else "off",
                            attributes={"friendly_name": "Comfee Lüfter läuft"})
        if "fan" in data:
            self.set_state("sensor.comfee_luefter_stufe_ist", state=data["fan"],
                            attributes={"friendly_name": "Comfee Lüfter Stufe (Gerät)"})
        if "mode" in data:
            self.set_state("sensor.comfee_luefter_modus_ist", state=data["mode"],
                            attributes={"friendly_name": "Comfee Lüfter Modus (Gerät, Rohwert)"})

    def _set_attribute(self, attr, value):
        cmd = [
            sys.executable, "/config/apps/midea_set.py",
            self.account, self.password, self.device_id, attr, str(value),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.log(f"SET {attr}={value} stdout: {result.stdout}")
            if result.returncode != 0:
                self.log(f"SET {attr}={value} stderr: {result.stderr}", level="WARNING")
        except Exception as e:
            self.error(f"Comfee Set Fehler ({attr}): {e}")

    def on_power_change(self, entity, attribute, old, new, kwargs):
        self._set_attribute("running", 1 if new == "on" else 0)
        self.run_in(self.poll, 5)

    def on_target_change(self, entity, attribute, old, new, kwargs):
        try:
            value = int(float(new))
        except (TypeError, ValueError):
            return
        self._set_attribute("target_humidity", value)
        self.run_in(self.poll, 5)

    def on_fan_change(self, entity, attribute, old, new, kwargs):
        try:
            value = int(float(new))
        except (TypeError, ValueError):
            return
        self._set_attribute("fan_speed", value)
        self.run_in(self.poll, 5)

    def on_mode_change(self, entity, attribute, old, new, kwargs):
        mapping = {
            "Manuell": 1,
            "Kontinuierlich": 2,
            "Smart": 3,
            "Trockner": 4,
        }
        if new not in mapping:
            return
        self._set_attribute("mode", mapping[new])
        self.run_in(self.poll, 5)
