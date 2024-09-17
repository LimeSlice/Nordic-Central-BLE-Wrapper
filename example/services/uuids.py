from pc_ble_driver_py.ble_driver import BLEUUID, BLEUUIDBase

"""
SUUID : BLE Service UUID
CUUID : BLE Characteristic UUID
"""


DIS_SUUID = BLEUUID(0x180A)
DIS_MANUFACTURE_NAME_CUUID = BLEUUID(0x2A29)
DIS_MODEL_NAME_CUUID = BLEUUID(0x2A24)
DIS_SERIAL_NUMBER_CUUID = BLEUUID(0x2A25)
DIS_FIRMWARE_REVISION_CUUID = BLEUUID(0x2A26)
DIS_HARDWARE_REVISION_CUUID = BLEUUID(0x2A27)
DIS_SOFTWARE_REVISION_CUUID = BLEUUID(0x2A28)
DIS_SYSTEM_ID_CUUID = BLEUUID(0x2A23)
DIS_IEEE_REGULATORY_CERTIFICATION_DATA_LIST_CUUID = BLEUUID(0x2A2A)
DIS_PNP_ID_CUUID = BLEUUID(0x2A50)

OPCODES_SUUID = BLEUUID(0x0001)
OPCODES_TX_CUUID = BLEUUID(0x0002)
OPCODES_RX_CUUID = BLEUUID(0x0003)
