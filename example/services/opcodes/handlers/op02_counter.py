#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Counter opcode handling
"""

from __future__ import annotations

import logging
import struct

from services.opcodes import OpCodesRxCharacteristic, OpCodesTxCharacteristic
from services.opcodes.opcode import OpCode

from dataclasses import dataclass


@dataclass
class CounterRxData:
    """Counter OpCode response model for validation of response"""

    count: int

    def __post_init__(self):
        self.valid = 0 <= self.count <= 0xFFFF

    @classmethod
    def parse_bytes(cls, payload):
        return CounterRxData(*struct.unpack("<H", payload))


class CounterOpCode(OpCode):

    def __init__(
        self,
        opcode_tx_char: OpCodesTxCharacteristic,
        opcode_rx_char: OpCodesRxCharacteristic,
        log_severity_level: int = logging.DEBUG,
    ):
        super().__init__(
            opcode_tx_char=opcode_tx_char,
            opcode_rx_char=opcode_rx_char,
            opcode=0x02,
            resp_data_len=4,
            log_severity_level=log_severity_level,
        )

    def write(self) -> CounterRxData:
        resp_data = self._write()

        try:
            return CounterRxData.parse_bytes(resp_data)
        except struct.error as e:
            self.logger.error("Failed to parse response data")
            raise e
