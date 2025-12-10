import socket
import logging
import time
import re

_LOGGER = logging.getLogger(__name__)


class AvalonMiniClient:
    """Low-level TCP client for the Avalon Mini 3 cgminer API."""

    def __init__(self, host: str, port: int = 4028, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout

    def _send_cmd(self, cmd: str) -> str:
        """Send a raw command string and return the response."""
        _LOGGER.debug("Sending command to Avalon Mini: %s", cmd)
        with socket.create_connection((self._host, self._port), timeout=self._timeout) as sock:
            sock.sendall(cmd.encode("ascii"))
            sock.shutdown(socket.SHUT_WR)
            chunks = []
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        response = b"".join(chunks).decode("ascii", errors="ignore")
        _LOGGER.debug("Received from Avalon Mini: %s", response)
        return response

    # --- Optional helpers for debugging/status ---

    def summary(self) -> str:
        return self._send_cmd("summary")

    def estats(self) -> str:
        return self._send_cmd("estats")

    # --- Power control ---

    def power_on(self) -> str:
        """
        Turn the device on (soft start).

        Uses the known syntax:
          ascset|0,softon,1:timestamp
        where timestamp is current UNIX epoch seconds.
        """
        timestamp = int(time.time())
        cmd = f"ascset|0,softon,1:{timestamp}"
        return self._send_cmd(cmd)

    def power_off(self) -> str:
        """
        Turn the device off / standby.

        Many guides show symmetric soft power like:
          ascset|0,softon,0:timestamp
        If your docs use a different command (e.g. 'softoff'),
        update this line accordingly.
        """
        timestamp = int(time.time())
        cmd = f"ascset|0,softoff,1:{timestamp}"  # TODO: adjust if your docs say 'softoff'
        return self._send_cmd(cmd)

    # --- Mode: Heating / Mining / Night ---

    def set_mode_index(self, index: int) -> str:
        """
        Set workmode by index.

        Typical mapping:
          0 = Heating
          1 = Mining
          2 = Night
        """
        cmd = f"ascset|0,workmode,set,{index}"
        return self._send_cmd(cmd)

    # --- Level: Eco / Super ---

    def set_level_index(self, index: int) -> str:
        """
        Set worklevel by index.

        Commonly:
          -1 = Eco
           0 = Super
        """
        cmd = f"ascset|0,worklevel,set,{index}"
        return self._send_cmd(cmd)

    # --- Display on/off ---

    def set_display(self, on: bool) -> str:
        """
        Toggle the front display.

        This is *device-specific*; replace with the exact command from
        your Avalon Mini 3 API documentation.

        Example placeholder:
          ascset|0,display,set,1  (on)
          ascset|0,display,set,0  (off)
        """
        value = 1 if on else 0
        cmd = f"ascset|0,display,set,{value}"  # TODO: adjust to your real display command
        return self._send_cmd(cmd)
        
    def get_status(self) -> dict:
        """
        Fetch and parse current status from 'estats'.

        Returns a dict with:
          - workmode: int (0=heating,1=mining,2=night)
          - worklevel: int (-1=eco,0=super)
          - softoff: int (0 or 1)
          - lcd_on: int (1 on, 0 off)
        and you can extend this with more fields later.
        """
        raw = self.estats()
        status: dict = {}

        # WORKMODE[0] WORKLEVEL[0] SoftOFF[0] LcdOnoff[1] ...
        m = re.search(r"WORKMODE\[(\-?\d+)\]", raw)
        if m:
            status["workmode"] = int(m.group(1))

        m = re.search(r"WORKLEVEL\[(\-?\d+)\]", raw)
        if m:
            status["worklevel"] = int(m.group(1))

        m = re.search(r"SoftOFF\[(\d+)\]", raw)
        if m:
            status["softoff"] = int(m.group(1))

        m = re.search(r"LcdOnoff\[(\d+)\]", raw)
        if m:
            status["lcd_on"] = int(m.group(1))

        return status

