#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Ping opcode handling
"""

import logging

from services.opcodes import OpCodesRxCharacteristic, OpCodesTxCharacteristic
from services.opcodes.opcode import OpCode


class PingOpCode(OpCode):

    def __init__(
        self,
        opcode_tx_char: OpCodesTxCharacteristic,
        opcode_rx_char: OpCodesRxCharacteristic,
        log_severity_level: int = logging.DEBUG,
    ):
        super().__init__(
            opcode_tx_char=opcode_tx_char,
            opcode_rx_char=opcode_rx_char,
            opcode=0x01,
            resp_data_len=0,
            log_severity_level=log_severity_level,
        )

    def write(self) -> None:
        self._write()
