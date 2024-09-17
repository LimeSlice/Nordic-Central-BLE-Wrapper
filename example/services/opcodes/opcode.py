#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Generic opcode object handling
"""

import logging
from queue import Queue, Empty

from services.opcodes import OpCodesTxCharacteristic, OpCodesRxCharacteristic


class OpCode:
    """Generic OpCode object for generating opcode commands with simple handling"""

    RESP_TIMEOUT_S = 10

    def __init__(
        self,
        opcode_tx_char: OpCodesTxCharacteristic,
        opcode_rx_char: OpCodesRxCharacteristic,
        opcode: int,
        resp_data_len: int,
        log_severity_level: int = logging.DEBUG,
    ):
        """Initialize OpCode object

        :param opcode_tx_char: Tx characteristic for writing data to the BLE peripheral
        :param opcode_rx_char: Rx characteristic for receiving notification responses
        :param opcode: op code object controls
        :param resp_data_len: expected response data length
        :param log_severity_level: logging level
        """
        assert 0x00 <= opcode <= 0xFF, "OpCode is a single-byte. Must be between 0x00 and 0xFF."
        assert resp_data_len < 20, "Data length must be less than 20 to adhere to MTU size."

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=log_severity_level)

        self.opcode_tx_char = opcode_tx_char
        self.opcode_rx_char = opcode_rx_char
        self.opcode = opcode
        self.resp_data_len = resp_data_len

        self.opcode_rx_char.add_opcode_handler(self.opcode, self.write_cb)
        self._resp_q = Queue()

    def _write(self, data: bytes = bytes()):
        self.opcode_tx_char.write(self.opcode, data)
        try:
            rx_data: bytes = self._resp_q.get(timeout=self.RESP_TIMEOUT_S)
        except Empty:
            self.logger.error("No response received for opcode 0x{:02X}".format(self.opcode))
            return None

        assert (
            len(rx_data) == self.resp_data_len
        ), f"Response data length does not match expected length. Received {len(rx_data)} expected {self.resp_data_len}."

        return rx_data

    def write(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet")

    def write_cb(self, opcode: int, data: bytes) -> None:
        assert (
            opcode == self.opcode
        ), "Notification handler received invalid opcode. Received 0x{:02X} expected 0x{:02X}.".format(
            opcode, self.opcode
        )
        self._resp_q.put(data)
