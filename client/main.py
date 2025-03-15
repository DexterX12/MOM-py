import json, pathlib
import Connection

config = None;

def set_connection(type, exchange):
    if type not in ["q", "t"]:
        return TypeError("Incorrect type specified")
    
    return Connection.Connection(type, exchange, config["MOM_SERVER_LOCATION"])


if __name__ == "__main__":
    path = pathlib.Path("client/config.json")
    with open(f"{pathlib.Path.absolute(path)}", "r") as file:
        config = json.load(file)
    
    cn = set_connection("q", "intercambio")

    cn.recv()
    


