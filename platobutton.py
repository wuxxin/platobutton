#!/usr/bin/env python3

import time

import click
import gattlib
import gattlib.uuid


plato_service = gattlib.uuid.gattlib_uuid_str_to_int(
    "e8f22220-9796-42a1-92ef-f65a7f9d6d79"
)
plato_read_uuid = gattlib.uuid.gattlib_uuid_str_to_int(
    "e8f20001-9796-42a1-92ef-f65a7f9d6d79"
)
plato_write_uuid = gattlib.uuid.gattlib_uuid_str_to_int(
    "e8f20002-9796-42a1-92ef-f65a7f9d6d79"
)


def terminal_input_available():
    return False


class StimDevice:

    mode_list = ["RL", "BL", "LR", "LB"]
    power_min = 800
    power_max = 1600
    minutes_min = 1
    minutes_max = 60
    mode_default = "LR"
    power_default = 1200
    minutes_default = 30

    def __init__(self, stim_mac):
        self.mac = stim_mac
        self.mode = self.mode_default
        self.power = self.power_default
        self.minutes = self.minutes_default
        self.device = gattlib.device.Device(adapter=None, addr=self.mac)

    def connect(self):
        self.device.connect()
        self.characteristics = self.device.characteristics

        if plato_read_uuid not in self.characteristics:
            raise RuntimeError("Not Found: plato_read_uuid '%s'" % plato_read_uuid)
        if plato_write_uuid not in self.characteristics:
            raise RuntimeError("Not Found: plato_write_uuid '%s'" % plato_write_uuid)
        self.read_handle = self.characteristics[plato_read_uuid]
        self.write_handle = self.characteristics[plato_write_uuid]

        self.firmware = self.cmd("F")[0]
        self.serial = self.cmd("#")
        return self.ping()

    def disconnect(self):
        self.device.disconnect()

    def cmd(self, cmdstring):
        value = False
        self.write_handle.write(bytearray(cmdstring, "utf-8"))
        value = self.read_handle.read()
        click.echo(
            "tdcs_event{device={},cmd={},result={}} {}".format(
                self.mac, cmdstring, value, int(time.time())
            )
        )
        return value

    def ping(self):
        return self.cmd("0/0")

    def start(self, mode, minutes):
        if minutes < self.minutes_min:
            minutes = self.minutes_min
        elif minutes > self.minutes_max:
            minutes = self.minutes_max

        stim_mode_start = "4,{0},{1},040,{2}/0".format(mode[0], mode[1], minutes * 60)
        return self.cmd(stim_mode_start)

    def power_change(self, p):
        if p < self.power_min:
            p = self.power_min
        elif p > self.power_max:
            p = self.power_max

        self.power = p
        return self.cmd("5,{0}".format(p // 10))

    def stop(self):
        return self.cmd("6/0")


@click.command()
@click.option("--device", help="Headset Mac Address, ([0-9A-Fa-f]{2}:){6}")
@click.option(
    "--mode",
    type=click.Choice(StimDevice.mode_list),
    help="TDCS Mode: RL=Create, BL=Rethink, LR=Learn, LB=Concentrate",
)
@click.option("--minutes", type=int, default=30, help="Duration in Minutes: 1-60")
@click.option(
    "--mikroampere", type=int, default=1200, help="Power in Mikroampere: 800-1600"
)
def cli(device, mode, minutes, mikroampere):
    """Start/Stop, select Mode, Duration and Power for Platoworks Headsets
get your device address using 'sudo hcitool lescan'
    """
    stim = StimDevice(device)
    stim.connect()

    try:
        status = stim.start(mode, minutes)
        stim_power = mikroampere
        start_time = time.time()
        stim_active = False
        stim_stopping = False

        while status[0] != "0" and status[0] != "7":
            time.sleep(1)
            if (time.time() - start_time > (minutes * 60)) and not stim_stopping:
                stim_stopping = True
                stim.stop()
            if status[0] == "5" and not stim_active:
                stim_active = True
                stim.power_change(stim_power)
            if terminal_input_available():
                key = click.getchar()
                if key == "s":
                    status = stim.stop()
                elif key == "+":
                    status = stim.power_change(stim_power + 100)
                    stim_power = stim.power
                elif key == "-":
                    status = stim.power_change(stim_power - 100)
                    stim_power = stim.power
                else:
                    status = stim.status()
            else:
                status = stim.status()
    except:
        while status[0] != "0" and status[0] != "7":
            status = stim.stop()
            time.sleep(1)
            status = stim.status()
            time.sleep(1)
        stim.disconnect()


if __name__ == "__main__":
    cli()
