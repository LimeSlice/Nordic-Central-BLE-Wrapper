# Nordic-Central-BLE-Wrapper

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[pc-ble-driver-py](https://github.com/NordicSemiconductor/pc-ble-driver-py) package wrapper for simple characteristic 
writing for testing peripherals or wrapping the tool for GUI integration or other CLI activity.

## Example

Provided is an example application that can:

- Read the Device Information service (DIS) characteristic values and save to an object
- Functionality for a simple custom OpCode service utilizing the generic Nordic UART service (NUS) to write opcodes 
  that provide custom functionality, then waits for a notification response, providing synchronous function calling.
- Example `main.py` for test usage:
  - Provide no arguments to output the enumerated list of detected Nordic devices in order to detect which COM port 
    (or `/dev/*` device if Linux).
  - Provide only a COM port without any target BLE MAC address to connect to to scan for available devices and output
    the BLE MAC addresses and its advertisement data.
  - Provide both a COM port and the BLE MAC address to go through the full flow of reading the Device Information 
    service data and write opcode values to provide a couple basic functions:
    - `"ping"`: ping the device and receive the same payload back
    - `"counter"`: receive a value that starts at 1 and increments every time the opcode is written to
    - `"delay"`: delays 5 seconds before sending back the notification response

## Usage

This example is meant to be forked imported to a separate repo for personal development for quick and clean BLE bring-up 
testing. Simply copy the `nordic_central_ble_wrapper` Python package to your project and build the service and 
characteristic classes you need for your application.
