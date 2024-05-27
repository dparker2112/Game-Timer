import pyudev
import time
import subprocess
import os
import shutil
import tempfile

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

def mount_drive(path):
    mount_point = tempfile.mkdtemp()
    subprocess.run(['sudo', 'mount', path, mount_point], check=True)
    return mount_point

def unmount_drive(mount_point):
    subprocess.run(['sudo', 'umount', mount_point], check=True)
    os.rmdir(mount_point)

def clear_directory(target_directory):
    for filename in os.listdir(target_directory):
        file_path = os.path.join(target_directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def should_skip_file(filename):
    # Skip hidden files and temporary files
    return filename.startswith('.') or filename.endswith(('.tmp', '~'))

def copy_drive(path, target_directory, overwrite=False):
    try:
        mount_point = mount_drive(path)
        if overwrite:
            if os.path.exists(target_directory):
                shutil.rmtree(target_directory)
            os.makedirs(target_directory)
        else:
            if not os.path.exists(target_directory):
                os.makedirs(target_directory)
            else:
                clear_directory(target_directory)
        for item in os.listdir(mount_point):
            if should_skip_file(item):
                #print(f"Skipping {item}")
                continue
            s = os.path.join(mount_point, item)
            d = os.path.join(target_directory, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print(f"Files copied to {target_directory}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        unmount_drive(mount_point)
def main():
    print(detect_usb_drives())


def cleanup():
    print("cleanup")

if __name__ == "__main__":
    try:
        main()
    except:
        cleanup()