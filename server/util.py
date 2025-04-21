import netifaces

def get_machine_ip():
        interfaces = netifaces.interfaces()
        interf = ""

        if ("enX" in interfaces):
            interf = "enX"
        elif ("en0" in interfaces):
            interf = "en0"
        else:
            interf = "eth0"
        
        addrs = netifaces.ifaddresses(interf)
        list_interfaces = addrs[netifaces.AF_INET]

        return list_interfaces[0]["addr"]
