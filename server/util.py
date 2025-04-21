import netifaces

def get_machine_ip():
        interfaces = netifaces.interfaces()
        print(interfaces)
