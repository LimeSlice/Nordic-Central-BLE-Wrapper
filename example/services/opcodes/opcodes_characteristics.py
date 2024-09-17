#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
OpCode service's Tx characteristic object
"""

from typing import Callable

import nordic_central_ble_wrapper as Ble
from services import uuids


class OpCodesTxCharacteristic(Ble.Characteristic):
    """OpCodes Tx Characteristic object for handling transferring data to the peripheral BLE device."""

    uuid = uuids.OPCODES_TX_CUUID

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for writing values

        :param nrf: Central BLE driver object used for BLE WRITE_REQ operations
        :param service: OpCodes service object
        """
        super().__init__(nrf=nrf, service=service)

    def write(self, opcode: int, data: bytes) -> None:
        """Write opcode and data buffer to characteristic."""
        assert 0x00 <= opcode <= 0xFF, "OpCode is a single-byte. Must be between 0x00 and 0xFF."
        assert len(data) < 20, "Data length must be less than 20 to adhere to MTU size."

        self.logger.debug("opcode: 0x{:02X}, data: {}".format(opcode, data.hex(sep=":")))
        super().write_request(payload=bytes([opcode]) + data)


class OpCodesRxCharacteristic(Ble.Characteristic):
    """OpCodes Rx Characteristic object for handling receiving notification responses from the peripheral BLE device."""

    uuid = uuids.OPCODES_RX_CUUID
    T_NtfHandler = Callable[[int, bytes], None]

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for handling responses from the peripheral BLE device

        :param nrf: Central BLE driver object used for handling notification responses
        :param service: OpCodes service object
        """
        super().__init__(nrf=nrf, service=service)

        self.ntf_handlers = dict()  # type: dict[int, OpCodesRxCharacteristic.T_NtfHandler]

    def add_opcode_handler(self, opcode: int, handler: T_NtfHandler) -> None:
        """Assign a handler for an opcode upon receiving a notification with the provided opcode.

        :param opcode: Opcode to assign to
        :param handler: Handler to assign to opcode
        """
        if opcode in self.ntf_handlers:
            self.logger.warning("Overwriting opcode handler for 0x{:02X}".format(opcode))

        self.ntf_handlers[opcode] = handler

    def remove_opcode_handler(self, opcode: int) -> None:
        """Remove handler for specified op code

        :param opcode: OpCode to remove
        """
        if opcode in self.ntf_handlers:
            self.ntf_handlers.pop(opcode)

    def on_notification(self, payload: bytes) -> None:
        try:
            self.ntf_handlers[payload[0]](payload[0], payload[1:])
        except KeyError:
            self.logger.error("Unknown opcode response. Opcode 0x{:02X} not handled.".format(payload[0]))
        except Exception as e:
            self.logger.error("Error handling opcode response. Opcode 0x{:02X} not handled.".format(payload[0]))
            raise e
