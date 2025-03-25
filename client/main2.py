import json, pathlib
import Connection

config = None

def set_connection(type, exchange, routing_key):
    if type not in ["q", "t"]:
        return TypeError("Incorrect type specified")
    
    return Connection.Connection(type, exchange, routing_key, config)


if __name__ == "__main__":
    path = pathlib.Path("config2.json")
    with open(f"{pathlib.Path.absolute(path)}", "r") as file:
        config = json.load(file)


    #Push Queue
    # cn = set_connection("q", "logs", "info")
    # cn.publish("Mensaje1", lambda x: print(f"Se envio, con respuesta: {x.json()}"))

    #Push topic
    cn = set_connection("t", "logs", "info")
    cn.publish("Mensaje4", lambda x: print(f"Se envio, con respuesta: {x}"))
    
    #Pull Queue
    # cn = set_connection("q", "logs", "info")
    # cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))

    #Subscribe topic
    cn = set_connection("t", "logs", "info")
    cn.subscribe( lambda x: print(f"Se envio, con respuesta: {x.json()}"))

    #Pull topic
    cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))

    # cn = set_connection("q", "logs", "info")
    # cn.subscribe( lambda x: print(f"Se envio, con respuesta: {x.json()}"))

    # cn = set_connection("q", "logs", "info")
    # #cn.subscribe( lambda x: print(f"Se envio, con respuesta: {x.json()}"))

    # #Pull topic
    # cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))


