import json, pathlib
import Connection

config = None;

def set_connection(type, exchange, routing_key):
    if type not in ["q", "t"]:
        return TypeError("Incorrect type specified")
    
    return Connection.Connection(type, exchange, routing_key, config)


if __name__ == "__main__":
    path = pathlib.Path("config.json")
    with open(f"{pathlib.Path.absolute(path)}", "r") as file:
        config = json.load(file)
    
    cn = set_connection("q", "logs", "info")

    #Este es push
    cn.publish("Mensaje1", lambda x: print(f"Se envio, con respuesta: {x.json()}"))
    cn = set_connection("q", "prueba", "warning")
    cn.publish("Mensaje2", lambda x: print(f"Se envio, con respuesta: {x}"))
    cn = set_connection("q", "logs", "info")
    cn.publish("Mensaje3", lambda x: print(f"Se envio, con respuesta: {x}"))
    # cn = set_connection("t", "logs", "info")
    # cn.publish("Mensaje4", lambda x: print(f"Se envio, con respuesta: {x}"))
    # cn = set_connection("t", "prueba", "warning")
    # cn.publish("Mensaje5", lambda x: print(f"Se envio, con respuesta: {x}"))
    
    # #Este es pull
    cn = set_connection("q", "logs", "info")
    cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))

    #subscribe
    # cn.subscribe()
    # cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))


