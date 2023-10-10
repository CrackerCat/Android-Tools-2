import os
import sys
import subprocess
import re

class Log:
    @staticmethod
    def send(msg):
        print('[Send] ' + msg)

    @staticmethod
    def print(msg):
        print(msg)

    @staticmethod
    def warn(msg):
        print('\033[0;33m' + msg + '\033[0m')

    @staticmethod
    def error(msg):
        print('\033[0;31m' + msg + '\033[0m')

def run_command(cmds, cwd='.'):
    return subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd).communicate()[0]

def cmd_adb_devices():
    return run_command(['adb', 'devices'])

def cmd_getprop_ro_build_fingerprint(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop', 'ro.build.fingerprint'])

def cmd_pm_list_packages_all(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user','0' , '-f', '-U'])

def cmd_pm_list_packages_third(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user','0' , '-f', '-3', '-U'])

def cmd_pm_list_packages_system(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'pm', 'list', 'packages', '--user','0' , '-f', '-s', '-U'])

def cmd_service_list(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'service', 'list'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'service', 'list'])

def cmd_lshal(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'lshal'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'lshal'])

def cmd_netstat_nlptu(serial_id, root_status):
    if root_status == 'su_root':
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])
    else:
        return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'netstat', '-nlptu'])

def cmd_dumpsys_package(serial_id, package_name):
    return run_command(['adb', '-s', serial_id, 'shell', 'dumpsys', 'package', package_name])

def cmd_adb_root(serial_id):
    return run_command(['adb', '-s', serial_id, 'root'])

def cmd_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'whoami'])

def cmd_getprop(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'getprop'])

def cmd_su_whoami(serial_id):
    return run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'whoami'])

def cmd_mkdir_sdcard_dump(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'mkdir', '/sdcard/.dump/'])

def cmd_mkdir_sdcard_dump_system(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'mkdir', '/sdcard/.dump/system/'])

def cmd_mkdir_sdcard_dump_vendor(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'mkdir', '/sdcard/.dump/vendor/'])

def cmd_rm_sdcard_dump(serial_id):
    run_command(['adb', '-s', serial_id, 'shell', 'rm', '-rf', '"/sdcard/.dump"'])

def dump_apk_folder(serial_id, package):
    run_command(['adb', '-s', serial_id, 'pull', package['path'][:package['path'].rindex('/')], package['package_name']], cwd='packages')

def dump_binary_folder(serial_id, binary_path, partition, cwd, root_status):
    if root_status == 'adb_root':
        dump_binary_folder_directly(serial_id, binary_path, cwd)
    else:
        if root_status == 'su_root':
            run_command(['adb', '-s', serial_id, 'shell', 'su', '-c', 'cp', '-r', binary_path, os.path.join('/sdcard/.dump/', partition)])
        else:
            run_command(['adb', '-s', serial_id, 'shell', 'cp', '-r', binary_path, os.path.join('/sdcard/.dump/', partition)])
        run_command(['adb', '-s', serial_id, 'pull', os.path.join('/sdcard/.dump/', binary_path[1:])], cwd=cwd)

def dump_binary_folder_directly(serial_id, binary_path, cwd):
    run_command(['adb', '-s', serial_id, 'pull', binary_path], cwd=cwd)

def dump_selinux_policy(serial_id):
    run_command(['adb', '-s', serial_id, 'pull', '/sys/fs/selinux/policy'], cwd='selinux')

def get_adb_privilege_status(serial_id):
    cmd_adb_root(serial_id)
    whoami = cmd_whoami(serial_id).decode('ascii').strip()
    if whoami == 'root':
        return 'adb_root'
    su_whoami = cmd_su_whoami(serial_id).decode('ascii').strip()
    if su_whoami == 'root':
        return 'su_root'
    else:
        return 'shell'

def adb_devices():
    output = cmd_adb_devices().decode('ascii')
    lines = output.split('\n')
    device_serial = []
    for line in lines:
        line = line.strip()
        if '\t' in line:
            id = line.split('\t')[0]
            status = line.split('\t')[1]
            if status == 'device':
                build_fingerprint = cmd_getprop_ro_build_fingerprint(id).decode('ascii').strip()
                root_status = get_adb_privilege_status(id)
            device_serial.append({'id': id, 'status': status, 'build_fingerprint': build_fingerprint, 'root_status': root_status})
    return device_serial

def select_adb_devices(pre_select_val):
    devices = adb_devices()
    i = 1
    Log.print('Please select an adb device:')
    for device in devices:
        if device['status'] == 'device':
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['build_fingerprint'] + '\t' + device['root_status'])
        else:
            Log.print(str(i) + ' => ' + device['id'] + '\t' + device['status'])
        i = i + 1
    if pre_select_val == -1:
        select = int(input())
    else:
        select = pre_select_val
    Log.print('You select device on line '+str(select))
    if select > len(devices):
        Log.error('Out of range.')
        return None
    if devices[select - 1]['status'] != 'device':
        Log.warn('Device not avaliable, status is: ' + devices[select - 1]['status'])
    elif devices[select - 1]['root_status'] != 'device':
        Log.warn('Non-root device, can only dump less binaries & libraries due to permission issue.')
    return devices[select - 1]

def is_privileged(package_info):
    return 'priv-app' in package_info['path']

def get_package_signature(dumpsys_package_output):
    pattern = r'signatures:\[([0-9a-fA-F, ]*)\]\,'
    search_result = re.search(pattern, dumpsys_package_output.decode('utf8'))
    signature = search_result.group(1)
    return signature

def get_package_selinux_label(package_info, dumpsys_package_output, platform_signature):
    if int(package_info['uid']) == 1000:
        return 'system_app'
    is_platform = platform_signature in get_package_signature(dumpsys_package_output)
    is_priv = is_privileged(package_info)
    if is_platform:
        return 'platform_app'
    if is_priv:
        return 'priv_app'
    return 'untrusted_app'

def get_packages(serial_id, pkg_filter_mode):
    if pkg_filter_mode == 1:
        pm_list_output = cmd_pm_list_packages_system(serial_id).decode('ascii')
    elif pkg_filter_mode == 2:
        pm_list_output = cmd_pm_list_packages_third(serial_id).decode('ascii')
    else:
        pm_list_output = cmd_pm_list_packages_all(serial_id).decode('ascii')
    lines = pm_list_output.split('\n')
    packages = []
    total = len(lines)
    i = 0
    android_dumpsys_package_output = cmd_dumpsys_package(serial_id, 'android')
    platform_signature = get_package_signature(android_dumpsys_package_output)
    for line in lines:
        line = line.strip().strip('package:')
        if '=' in line and ' ' in line:
            path = line[:line.rindex('=')]
            package_name = line[line.rindex('=') + 1:line.rindex(' ')]
            uid = line[line.rindex(' ') + 1:].strip('uid:')
            if ',' in uid:
                uid = uid.split(',')[0]
            package_dumpsys_package_output = cmd_dumpsys_package(serial_id, package_name)
            package_info = {}
            package_info['package_name'] = package_name
            package_info['path'] = path
            package_info['uid'] = uid
            package_info['label'] = get_package_selinux_label(package_info, package_dumpsys_package_output, platform_signature)
            packages.append(package_info)
            show_progress(i, total, 'Collect package info for ' + package_name)
        i = i + 1
            
    return packages

def show_progress(now, total, msg):
    if total == 0:
        return
    p = (now * 100) // total
    Log.print('[' + str(p) + '%' + '] ' + msg)


def main():
    is_info_only = False
    pkg_filter_mode = 0
    if len(sys.argv) >= 2:
        if sys.argv[1] == '-i' or sys.argv[1] == '--info-only':
            is_info_only = True
            Log.print('-i or --info-only detected: will not dump apks, libraries and binaries.')
        elif sys.argv[1] == '-s' or sys.argv[1] == '--system-app-only':
            pkg_filter_mode = 1
            Log.print('-s or --system-app-only detected: will only dump system packages.')
        elif sys.argv[1] == '-3' or sys.argv[1] == '--third-party-only' :
            pkg_filter_mode = 2
            Log.print('-3 or --third-party-only detected: will only dump third party packages.')

    device_info = select_adb_devices(-1)
    serial_id = device_info['id']
    root_status = device_info['root_status']

    Log.print('[Task 1] Dump Android framework & Apps')

    packages = get_packages(serial_id, pkg_filter_mode)
    os.makedirs('packages', exist_ok=True)
    package_index_file = open('package_index.csv', 'w')
    package_index_file.write('package_name,path,uid,label\n')
    total = len(packages)
    i = 0
    for package in packages:
        package_index_file.write(package['package_name']+','+package['path']+','+package['uid']+','+package['label']+'\n')
        package_index_file.flush()
        if not is_info_only:
            dump_apk_folder(serial_id, package)
            show_progress(i, total, 'Dump package binaries for ' + package['package_name'])
        i = i + 1
    
    package_index_file.close()

    Log.print('[Task 2] Dump SELinux & seccomp policy')
    os.makedirs('selinux', exist_ok=True)
    dump_selinux_policy(serial_id)

    Log.print('[Task 3] Run useful commands')
    service_list_file = open('service_list.txt', 'wb')
    service_list_file.write(cmd_service_list(serial_id, root_status))
    service_list_file.close()

    lshal_file = open('lshal.txt', 'wb')
    lshal_file.write(cmd_lshal(serial_id, root_status))
    lshal_file.close()

    netstat_file = open('netstat.txt', 'wb')
    netstat_file.write(cmd_netstat_nlptu(serial_id, root_status))
    netstat_file.close()

    getprop_file = open('getprop.txt', 'wb')
    getprop_file.write(cmd_getprop(serial_id))
    getprop_file.close()

    if not is_info_only:
        os.makedirs('system_libs', exist_ok=True)
        os.makedirs('vendor_libs', exist_ok=True)
        os.makedirs('system_binaries', exist_ok=True)
        os.makedirs('vendor_binaries', exist_ok=True)
        if root_status != 'adb_root':
            cmd_mkdir_sdcard_dump(serial_id)
            cmd_mkdir_sdcard_dump_system(serial_id)
            cmd_mkdir_sdcard_dump_vendor(serial_id)
        
        Log.print('[Task 4] Dump libraries')
        dump_binary_folder_directly(serial_id, '/system/lib64/', 'system_libs')
        dump_binary_folder_directly(serial_id, '/system/lib/', 'system_libs')
        dump_binary_folder(serial_id, '/vendor/lib64/', 'vendor', 'vendor_libs', root_status)
        dump_binary_folder(serial_id, '/vendor/lib/', 'vendor', 'vendor_libs', root_status)

        Log.print('[Task 5] Dump binaries')
        dump_binary_folder(serial_id, '/system/bin/', 'system', 'system_binaries', root_status)
        dump_binary_folder(serial_id, '/vendor/bin/', 'vendor', 'vendor_binaries', root_status)

        if root_status != 'adb_root':
            cmd_rm_sdcard_dump(serial_id)

if __name__ == '__main__':
    main()
    # test_dump_vendor()