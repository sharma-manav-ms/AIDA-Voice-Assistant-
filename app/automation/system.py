"""
system.py
---------
System-level controls: power, volume, brightness, battery, etc.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
from typing import Optional

import psutil

from app.config.settings import VOLUME_STEP, BRIGHTNESS_STEP
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SystemController:
    """
    Operating-system level operations for Windows.
    """

    # ══════════════════════════════════════════════════════════
    #  Power
    # ══════════════════════════════════════════════════════════

    def shutdown(self, delay: int = 30) -> str:
        """Schedule system shutdown."""

        logger.info("Shutdown scheduled in %d seconds.", delay)
        os.system(f"shutdown /s /t {delay}")
        return f"Your PC will shut down in {delay} seconds."

    def restart(self, delay: int = 10) -> str:
        """Schedule system restart."""

        logger.info("Restart scheduled in %d seconds.", delay)
        os.system(f"shutdown /r /t {delay}")
        return f"Your PC will restart in {delay} seconds."

    def cancel_shutdown(self) -> str:
        """Cancel a pending shutdown or restart."""

        os.system("shutdown /a")
        return "Shutdown cancelled."

    def sleep(self) -> str:
        """Put the system to sleep."""

        logger.info("System going to sleep.")

        # SetSuspendState(hibernate, force, wakeupEventsDisabled)
        ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
        return "Putting your PC to sleep."

    def lock(self) -> str:
        """Lock the workstation."""

        logger.info("Locking workstation.")
        ctypes.windll.user32.LockWorkStation()
        return "PC locked."

    # ══════════════════════════════════════════════════════════
    #  Volume (using pycaw)
    # ══════════════════════════════════════════════════════════

    def _get_volume_interface(self):
        """Return the Windows audio endpoint volume interface."""

        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None,
            )

            return interface.QueryInterface(IAudioEndpointVolume)
        except Exception as exc:
            logger.error("Volume control unavailable: %s", exc)
            return None

    def volume_up(self, step: int = VOLUME_STEP) -> str:
        """Increase system volume."""

        vol = self._get_volume_interface()

        if vol is None:
            return "Volume control is not available."

        current = vol.GetMasterVolumeLevelScalar()
        new_level = min(1.0, current + step / 100)
        vol.SetMasterVolumeLevelScalar(new_level, None)

        percent = int(new_level * 100)
        return f"Volume set to {percent}%."

    def volume_down(self, step: int = VOLUME_STEP) -> str:
        """Decrease system volume."""

        vol = self._get_volume_interface()

        if vol is None:
            return "Volume control is not available."

        current = vol.GetMasterVolumeLevelScalar()
        new_level = max(0.0, current - step / 100)
        vol.SetMasterVolumeLevelScalar(new_level, None)

        percent = int(new_level * 100)
        return f"Volume set to {percent}%."

    def mute_toggle(self) -> str:
        """Toggle system mute."""

        vol = self._get_volume_interface()

        if vol is None:
            return "Volume control is not available."

        current_mute = vol.GetMute()
        vol.SetMute(not current_mute, None)

        return "Unmuted." if current_mute else "Muted."

    def get_volume(self) -> str:
        """Get current volume level."""

        vol = self._get_volume_interface()

        if vol is None:
            return "Volume control is not available."

        level = int(vol.GetMasterVolumeLevelScalar() * 100)
        return f"Current volume is {level}%."

    # ══════════════════════════════════════════════════════════
    #  Brightness
    # ══════════════════════════════════════════════════════════

    def brightness_up(self, step: int = BRIGHTNESS_STEP) -> str:
        """Increase screen brightness."""

        try:
            import screen_brightness_control as sbc

            current = sbc.get_brightness(display=0)

            if isinstance(current, list):
                current = current[0]

            new_level = min(100, current + step)
            sbc.set_brightness(new_level, display=0)

            return f"Brightness set to {new_level}%."

        except Exception as exc:
            logger.error("Brightness control failed: %s", exc)
            return "Brightness control is not available on this display."

    def brightness_down(self, step: int = BRIGHTNESS_STEP) -> str:
        """Decrease screen brightness."""

        try:
            import screen_brightness_control as sbc

            current = sbc.get_brightness(display=0)

            if isinstance(current, list):
                current = current[0]

            new_level = max(0, current - step)
            sbc.set_brightness(new_level, display=0)

            return f"Brightness set to {new_level}%."

        except Exception as exc:
            logger.error("Brightness control failed: %s", exc)
            return "Brightness control is not available on this display."

    # ══════════════════════════════════════════════════════════
    #  System Info
    # ══════════════════════════════════════════════════════════

    def get_battery(self) -> str:
        """Report battery status."""

        battery = psutil.sensors_battery()

        if battery is None:
            return "No battery detected — are you on a desktop?"

        percent = battery.percent
        plugged = "plugged in" if battery.power_plugged else "on battery"

        if battery.secsleft != psutil.POWER_TIME_UNLIMITED and \
           battery.secsleft > 0:
            hours = battery.secsleft // 3600
            minutes = (battery.secsleft % 3600) // 60
            time_left = f", about {hours}h {minutes}m remaining"
        else:
            time_left = ""

        return f"Battery is at {percent}%, {plugged}{time_left}."

    def get_system_info(self) -> str:
        """Return a brief system summary."""

        uname = platform.uname()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()

        ram_used = mem.used / (1024 ** 3)
        ram_total = mem.total / (1024 ** 3)

        return (
            f"System: {uname.system} {uname.release}. "
            f"Processor: {uname.processor}. "
            f"CPU usage: {cpu_percent}%. "
            f"RAM: {ram_used:.1f} GB used of {ram_total:.1f} GB."
        )
