import pyudev
import time

def detect_drives():
    context = pyudev.Context()
    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        print(device.get('ID_FS_LABEL', 'unlabeled partition'))

def detect_usb_drives():
    context = pyudev.Context()
    path = None
    for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
        properties = device.properties
        if properties.get('ID_BUS') == 'usb':
            # This checks if the device is a USB device
            #print(f"Found USB Device: {device.device_node}")
            path = device.device_node
            # device.device_node will contain the device identifier, e.g., /dev/sdb1

            # Additional useful properties
            #print(f"  Device Name: {device.get('ID_FS_LABEL', 'Unknown')}")
            #print(f"  Device Type: {device.get('ID_FS_TYPE', 'Unknown')}")
            #print(f"  Serial: {device.get('ID_SERIAL', 'Unknown')}")
    return path

def main():
    print(detect_usb_drives())


def cleanup():
    print("cleanup")

if __name__ == "__main__":
    try:
        main()
    except:
        cleanup()