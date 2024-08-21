#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
BLE Service object
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pc_ble_driver_py import ble_driver as NordicDriver

if TYPE_CHECKING:
  from central_ble_driver import CentralBleDriver
  from characteristic import Characteristic


class Service:
  """Service interface for handling different characteristics per service
  """

  uuid = None                 # type: (NordicDriver.BLEUUID | None)
  characteristics = dict()    # type: dict[NordicDriver.BLEUUID, Characteristic]

  def __init__(self, nrf: CentralBleDriver) -> None:
    self.nrf = nrf
    self.logger = logging.getLogger(self.__class__.__name__)

