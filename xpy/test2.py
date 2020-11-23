import sys
import subprocess


def execute(option, *machines):
    for machine in machines:
        print(option,machine)
        result = subprocess.call(['ping', '-n', '1', '-w', '100', machine])
        if not result:
            print("Address {} OK".format(machine))
        else:
            print("echec: ",result)


OS = sys.platform

option = '-n' if OS != 'win32' else ''

execute(option, '192.168.1.43', '12.250.120.63')