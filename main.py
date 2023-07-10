import platform
import subprocess
import psutil
import win32com.client
import winreg
import pyodbc
import socket
from datetime import datetime
import wmi
"""  
Requisitos para atualização para windows 11:  

Processador:  
    -1 GHz ou mais  
    -2 ou mais núcleos  
    -64 Bits  
Sistema operativo:  
    -Windows 10, versão 2014 ou superior  
4 GB de RAM ou mais  
Armazenamento de 64 GB ou superior  
Boot:  
    -Arranque seguro  
    -UEFI  
TPM 2.0
Placa Gráfica compativel com DirectX 12 ou superior com controlador WDDM 2.0
"""



# Obter codigo da maquina
computer_id = socket.gethostname()

# Obter a data
now = datetime.now()

date = now.strftime("%Y-%m-%d %H:%M:%S")

# Obter informações do pc
c = wmi.WMI()

comp = c.Win32_ComputerSystem()[0]

pc_manufacturer = comp.Manufacturer
pc_model = comp.Model

# Verificar a velocidade e os núcleos dos processadores
def cpu_check():
    global core_count
    core_count = psutil.cpu_count(logical=False)
    global cpu_freq
    cpu_freq = round(psutil.cpu_freq().current / 1000, 2)
    global cpu_arch
    cpu_arch = platform.architecture()[0]
    if (core_count >= 2 and cpu_freq >= 1.0 and cpu_arch == "64bit"):
        return True
    return False


# Verificar sistema operativo
def OS_check():
    global OS_version
    os_version = int(platform.version().split('.')[2])
    if os_version >= 19041:
        OS_version = platform.version()
        return True
    return False


# Verificar RAM
def RAM_check():
    mem_info = psutil.virtual_memory()
    global total_RAM
    total_RAM = round(mem_info.total / 1024 ** 3, 0)
    if total_RAM >= 4.0:
        return True
    return False


# Obter tamanho dos discos
def get_disks_size():
    partitions = psutil.disk_partitions()
    disk_space = []

    for partition in partitions:
        try:
            disk = psutil.disk_usage(partition.mountpoint)
            disk_space.append((partition.device, disk.total, disk.free))
        except PermissionError:
            pass
    return disk_space


# Verificar tamanho dos discos
def disk_size_check():
    aux = 0
    for disk in disk_size_info:
        device, total, free = disk
        total = round(total / 1024 ** 3, 0)
        free = round(free / 1024 ** 3, 0)
        if total >= 64:
            global disks_available
            disks_available.append(device)
            if free > 25:
                aux += 1
            else:
                global free_space
                free_space.append(f"{device}: only {free} GB free")
        else:
            global total_space
            total_space.append(f"{device}: only {total} GB capacity")
    if aux > 0:
        return True
    return False


# Verificar se UEFI está ativo
def uefi_check():
    wmi = win32com.client.GetObject("winmgmts:")
    computer_system = wmi.ExecQuery("SELECT * FROM Win32_ComputerSystem")[0]

    uefi_status = computer_system.BootupState
    if uefi_status == "Normal boot":
        return True
    return False


# Verificar se o Arranque seguro está ativo
def secure_boot_check():
    key_path = r"SYSTEM\CurrentControlSet\Control\SecureBoot\State"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
        value, _ = winreg.QueryValueEx(key, "UEFISecureBootEnabled")
        return bool(value)
    except FileNotFoundError:
        return False


# Verificar se TPM está na versão 2.0
def tpm_check():
    tpm_status = False
    try:
        tpm_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Enum\\ACPI\\MSFT0101")
        tpm_status = True
    except FileNotFoundError:
        pass
    return tpm_status


# Verificar se é compativel com directX12 com o controlador WDDM 2.0 ou superior
def get_driver_version():
    try:
        cmd = 'wmic path Win32_VideoController get DriverVersion /format:value'
        output = subprocess.check_output(cmd, shell=True, encoding='utf-8')
        driver_version = output.strip().split('=')[1]

        # Obter apenas os primeiros dois números da versão
        version_numbers = driver_version.split('.')
        driver_model = '.'.join(version_numbers[:2])

        return driver_model
    except Exception as e:
        return False

try:
    driver_version = float(get_driver_version())/10
except ValueError:
    driver_version = -1


def driver_check():
    if driver_version >= 2.0:
        return True
    return False


# Variáveis globais para colocar no csv
# Core
core_count = 0
cpu_freq = 0.0
cpu_arch = ""
# OS
OS_version = 0
# RAM
total_RAM = 0
# Memoria
disks_available = []
disk_size_info = get_disks_size()
free_space = []
total_space = []

report_string = ""

if not cpu_check():
    report_string += "CPU does not comply the requirements(2 cores, 1.0 GHz and 64 bit)\t"

if not OS_check():
    report_string += "The OS is not compatible to update(Min version: 10.0.19045)\t"

if not RAM_check():
    report_string += "The minimum RAM is 4 GB\t"

if len(free_space) > 0:
    report_string += f"Full disks(Min: 25 GB free): {free_space}\t"
if len(total_space) > 0:
    report_string += f"Disks without capacity(Min: 64 GB): {total_space}\t"


uefi_string = ""
if uefi_check():
    uefi_string = "Enabled"
else:
    uefi_string = "Desabled"


secure_boot_string = ""
if secure_boot_check():
    secure_boot_string = "Enabled"
else:
    secure_boot_string = "Desabled"


tpm_string = ""
if tpm_check():
    tpm_string = "Rigth version"
else:
    tpm_string = "Not right version"

driver_check()
if driver_version == -1:
    report_string += "We could not detect your WDDM version\t"
if not driver_check():
    report_string += "The minimum WDDM version is 2.0"

if report_string == "":
    report_string = None

isReady = ""
if cpu_check() and OS_check() and RAM_check() and disk_size_check() and uefi_check() and secure_boot_check() and secure_boot_check() and tpm_check() and driver_check():
    isReady = 1
else:
    isReady = 0


disk_string = ""
for disk in disks_available:
    disk_string += f"{str(disk)}\t"

# Conecção com BD
connection_string = "DRIVER={SQL Server};Server=pttrfdev;Database=WhyNotWin11;UID=whynotwin11;PWD=Start.12345"

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Inserir dados na BD
sql  = f"insert into Report values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

values = (computer_id, date, pc_manufacturer, pc_model, core_count, cpu_freq, cpu_arch, OS_version, total_RAM, disk_string, uefi_string, secure_boot_string, tpm_string, driver_version, isReady, report_string)

cursor.execute(sql, values)
conn.commit()

conn.close()


