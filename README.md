## Materia: ST0263-251

### Integrantes del proyecto:

Delvin Rodríguez Jiménez - djrodriguj@eafit.edu.co

Wendy Benítez Gómez - wdbenitezg@eafit.edu.co

Fredy Cadavid Franco - fcadavidf@eafit.edu.co

### Profesor
Edwin Nelson Montoya Múnera - emontoya@eafit.edu.co

# Message-Oriented Middleware
Este middleware está diseñado para la comunicación  y transferencia de mensajes entre clientes, aplicando principios de sistemas distribuidos.

## Índice

- [Análisis y requerimientos iniciales](#análisis-y-requerimientos-iniciales)
- [Diseño y elección de patrones](#diseño-y-elección-de-patrones)
	- [Mensajería, colas y tópicos](#mensajería-colas-y-tópicos)
	- [Autenticación](#autenticación)
	- [Arquitectura y Detalles](#arquitectura-y-detalles)
- [Desarrollo en entorno local](#desarrollo-en-entorno-local)
	- [Instalación](#instalación)
		- [Servidor](#servidor)
		- [Replicación](#replicación)
		- [Autenticación](#autenticación)
		- [Particionamiento](#particionamiento)
		- [Cliente](#cliente)
- [Despliegue en producción](despliegue-en-producción)
	- [Composición y direccionamiento](#composición-y-direccionamiento)
	- [Configuración y descripción de parámetros](#configuración-y-descripción-de-parámetros)
		- [Funciones Lambda](#funciones-lambda)
		- [Grupos de seguridad](#grupos-de-seguridad)
	- [Lanzar servidores](#lanzar-servidores)
		- [Cliente y uso del software](#cliente-y-uso-del-software)
- [Referencias](#referencias)

## Análisis y requerimientos iniciales
El foco de este trabajo se centra en la implementación de un servicio de mensajería similar a servicios como *Apache Kafka* y *RabbitMQ*, con un enfoque en la **Tolerancia a fallos**, concepto comúnmente trabajado en sistemas distribuidos.
Los requerimientos funcionales iniciales consisten en garantizar la comunicación de varios clientes a través de colas y tópicos.

![Flujo básico de comunicación en MOMs](https://i.imgur.com/rTS0IbU.png)

*Figura 1: Flujo básico de comunicación en MOMs**¹***

Además, para asegurarse de que la comunicación solo se realiza entre usuarios autorizados, el servicio debe implementar algún tipo de autenticación.
Finalmente, respecto al aspecto no funcional, se debe implementar mecanismos para garantizar la tolerancia a fallos, mecanismos presentes en sistemas distribuidos como la ***replicación y particionamiento*** de los datos, además de la forma en como estos son replicados y particionados.

En la siguiente sección se presentará las decisiones tomadas para un acercamiento a la implementación de estos requerimientos.
## Diseño y elección de patrones
Respecto a la parte funcional, se tomaron en cuenta los siguientes aspectos:
#### Mensajería, colas y tópicos
* Los mensajes son identificados mediante una llave o *routing key*, permitiendo el enrutamiento de estos a sus correspondientes colas/tópicos.
* Cada tópico o cola hace parte de un *exchange*, el cual permite el proceso de enrutamiento de cada uno de los mensajes.
* Cada instancia de MOM posee una lista de usuarios "suscritos" a un tópico, creando una cola especial para cada usuario suscrito. Esto a su vez utiliza el ***mecanismo de pull***, donde cada cliente es responsable de verificar la existencia de nuevos mensajes en el tiempo.
#### Autenticación
* El ingreso de usuarios nuevos a la base de datos es manual, por lo que no se ha implementado un frontend que permita el registro de usuarios.
* Cualquier acción dentro de cada servicio de MOM requiere autenticación a partir de **tokens**, utilizando JWT, el cual es *stateless*.
* Cada usuario que inicie sesión, es asignado un token, donde puede realizar acciones de productor y suscriptor a través de dicho token.

Respecto a la parte no funcional y temas de arquitectura, se tiene lo siguiente:
#### Arquitectura y Detalles
El servicio está desarrollado en su totalidad en Python, utilizando gRPC como protocolo de comunicación entre los nodos de servicio de MOM, además de la comunicación a través de API REST entre cliente-MOM. Esta arquitectura se orquestó con el concepto de ***tolerancia a fallos*** en mente, donde se establece un servicio de particionamiento para asignar los mensajes a partir de sus identificadores a los nodos correspondientes y, un servicio de replicación en cada nodo MOM para garantizar la redundancia y consistencia de los datos.

![Arquitectura principal](https://i.imgur.com/mh4K53r.png)

*Figura 2: Arquitectura principal del servicio*

Los nodos MOM poseen por aparte un servicio de replicación el cual utiliza gRPC para la comunicación. Cada nodo es cliente y servidor a la vez, permitiendo recibir peticiones de replicación por parte de otros nodos, y tener la capacidad de enviar peticiones a otros.

Las peticiones que los clientes realizan para suscribirse o publicar en algún tópico o cola son redireccionados a través de la API Gateway, de AWS, utilizando una función Lambda, también, de AWS. La necesidad del redireccionamiento proviene del principio de particionamiento; es necesario llevar el mensaje que el cliente necesita entregar a la cola o tópico correspondiente, sin importar en el nodo en que se encuentre, y este proceso debe ser transparente para el usuario. Por esta razón, se aplicó la siguiente arquitectura de localización de la información:

![Localización de la información](https://i.imgur.com/OCggPAx.png)

*Figura 3: Enrutamiento de la información²*

En el caso de este proyecto, el routing tier es la API Gateway, la cual a través de una función Lambda, le pregunta al servicio de particionamiento (que funciona en el nodo como un servicio junto a ZooKeeper), que nodo le pertenece la *routing key* del mensaje entrante, para luego devolver la dirección del MOM y reenviar la petición. Finalmente, la respuesta es devuelta al cliente que originalmente inició la petición.

Respecto al aspecto de autenticación, se tiene un servicio de auth para verificar si el usuario que está realizando la operación está autenticado, realizando una verificación mediante *tokens*, pues se usa JWT. Por cada petición, se debe presentar el token generado al momento de iniciar sesión (es decir, al establecer la conexión por primera vez)

Para mantener control de qué nodos existen y cuáles son lideres de cada partición para garantizar el correcto orden de replicación, se utiliza **Apache ZooKeeper**, el cual posee una estructura inspirada en sistemas de archivos, lo que permite guardar de manera estructurada la información de los nodos que hagan parte del servicio, además de la capacidad de obtener cambios en la topología en tiempo real, y algoritmos de elección de lider.

![Estructura de control](https://i.imgur.com/kebebLU.png)

*Figura 4: Control de nodos MOM mediante ZooKeeper*

Cada uno de los nodos le ofrece a ZooKeeper la metadata relevante para la comunicación de mensajes, así como para temas de particionamiento y replicación.

## Desarrollo en entorno local
Este proyecto requiere ***al menos*** Python 3.10, utilizando las siguientes librerías:
* **kazoo:** API de comunicación para ZooKeeper
* **sqlite3:** API de base de datos para registro (manual) de usuarios 
* **grpc & grpc-tools:** API de comunicación utilizando el protocolo gRPC, además de las herramientas para compilar los archivos .proto
* **flask:** Exponer una API REST a través de un servidor HTTP
* **jwt:** Autenticación mediante tokens
* **netifaces:** Manejo de interfaces de red, principalmente para la obtención de direcciones IP de adaptadores de red.

El archivo requirements.txt posee todas las librerías necesarias para su ejecución.

Además de Python, se utiliza **Apache ZooKeeper** en su versión 3.8.4, la última versión estable recomendada al día de esta publicación (04/20/2025).

La comunicación entre consumidores y 	MOMs es gracias a la **API Gateway** de AWS, el cual funciona como intermediario para enrutar los mensajes y autenticar los usuarios. Esto se puede reemplazar utilizando flask como servidor intermediario.


### Instalación
El repositorio posee archivos `.sh` dentro del directorio `/config` que permiten configurar y ejecutar cada servidor de manera individual como un servicio utilizando systemd. Esto garantiza que se ejecuten en el fondo y puedan reiniciarse en caso de errores/reinicios de máquina.

Dentro de cada archivo `.service` existe una estructura como la siguiente:
```bash
[Unit]
Description=API Auth Service
After=network.target

[Service]
ExecStart=/home/ubuntu/MOM-py/.venv/bin/python3 /home/ubuntu/MOM-py/auth/main.py
WorkingDirectory=/home/ubuntu/MOM-py/auth
Restart=always
User=ubuntu
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
Es necesario que, previo a la instalación de los servicios, exista un entorno virtual creado, con las librerías previamente instaladas. Se destaca el hecho de que la ruta del entorno virtual y del proyecto pueden variar, se debe revisar para cada servicio la ruta correcta para crear correctamente los servicios. Por defecto, se crean los entornos con el nombre de `.venv` y el proyecto vive en el home del usuario `ubuntu`.

#### Servidor
Dentro del directorio `/server` se encuentran los archivos para ejecutar un nodo MOM.
Para ejecutar el servicio de mensajería se utiliza el siguiente comando: `python main.py {port}` donde PORT indica el puerto en el cual se desea exponer el servidor (por defecto será el puerto 5000). Cada petición de mensaje que llegue al servidor será registrada automáticamente por el servicio de ZooKeeper.

Por defecto, la URL de conexión con ZooKeeper, y el nombre de los *path* donde se guardan las particiones y nodos se encuentran en el archivo de configuración `config.json`, que tiene este aspecto por defecto:
```json
{
"ZOOKEEPER_LOCATION":  "127.0.0.1:2181",
"NODES_LOCATION":  "/connected/",
"PARTITIONS_LOCATION":  "/partitions/"
}
```

Dentro del directorio `/server/grpc_replication` se encuentran los archivos para el servicio de replicación. El archivo `replication.proto` establece los métodos y tipos de mensaje. Por defecto, este servicio se ejecuta en conjunto con el servidor MOM, y es éste el que se encarga de enviar cada nuevo mensaje de algún MOM a todos los demás.

#### Replicación
Dentro del mismo directorio del servidor `/server/grpc_replication` se encuentra el servidor de replicación, `replicator_server.py`. Este se debe ejecutar en la misma máquina donde se encuentra cada servidor MOM. Este hace parte de un módulo, por lo que se debe ejecutar de la siguiente manera: `python -m grpc_replication.replicator_server`, donde el working directory debe ser dentro de `/server`. Por defecto, escucha en el puerto `50051`

#### Autenticación
Dentro del directorio `/auth` se tiene el servidor encargado de la autenticación de las peticiones generadas por usuarios. Para ejecutarlo, se utiliza el siguiente comando: `python main.py`. Escucha por defecto en el puerto `5000`

Para ejecutar el servicio de autenticación, es necesario brindar una *secret key* que permita decodificar el token, esta se debe provisionar como una variable de entorno, la cual es identificada como `FLASK_SECRET_KEY`

#### Particionamiento
Dentro del directorio `/partitioning_service` está el servicio de particionamiento, el cual se ejecuta con  `python main.py`. Este servidor debería estar corriendo en el mismo nodo de ZooKeeper, para asistir al Routing Tier en la localización de los nodos. Escucha por defecto en el puerto `5000`

#### Cliente
Dentro del directorio `/client` se encuentran los archivos para realizar la conexión hacia el servidor. Dentro del archivo `config.json` se encuentra la configuración de conexión: la URL de la API, y el usuario y contraseña del cliente que ha sido previamente registrado.

```json
{
    "API_SERVER_LOCATION": "http://127.0.0.1:8080",
    "USERNAME": "admin",
    "PASSWORD": "admin"
}
```
Dentro del mismo directorio se encuentra el archivo `Connection.py` el cual se encarga de establecer la comunicación y conexión inicial, además de la autenticación hacia el servidor. Este archivo es necesario para cualquier conexión, en caso de probar conexiones manuales. El archivo `main.py` posee un ejemplo con diferentes mensajes. Para ejecutar el cliente, se utiliza el siguiente comando dentro del directorio `/client`:

    python main.py

Para un ejemplo más exhaustivo, léase la sección de guía en la parte de despliegue.

## Despliegue en producción

### Composición y direccionamiento
El despliegue en producción se realizó en AWS. Está compuesto por las siguientes máquinas, seguido de sus direcciones:

Máquinas EC2
* MOM 1: Máquina de servidor MOM para el procesamiento de los mensajes.  - 172.31.81.164
* MOM 2: Máquina de servidor MOM para el procesamiento de los mensajes. - 172.31.80.113
* MOM 3: Máquina de servidor MOM para el procesamiento de los mensajes. - 172.31.93.145
* ZooKeeper y Partitioning Service - 172.31.25.120
* Servicio de autenticación - 172.31.25.86

API Gateway
* Autenticación: **[https://3hf9pm7wjd.execute-api.us-east-1.amazonaws.com/auth](https://3hf9pm7wjd.execute-api.us-east-1.amazonaws.com/auth)**
* Envio de mensajes: **[https://3hf9pm7wjd.execute-api.us-east-1.amazonaws.com/send](https://3hf9pm7wjd.execute-api.us-east-1.amazonaws.com/send)**

Todas las máquinas se encuentran dentro de la red privada, puesto que se define una API Gateway que permite la conexión a los servicios de manera interna. Para lograr esto, se utilizó dos funciones Lambda, nombradas "sendPartition" para el envío de mensajes, el cuál lo activa el endpoint `/send`, y la función "authUser", que autentica los usuarios, activándolo el endpoint `/auth`

![Funciones Lambda](https://i.imgur.com/Yxdau2v.png)


![Instancias en AWS](https://i.imgur.com/u94JGQQ.png)


### Configuración y descripción de parámetros

#### Funciones Lambda
Como se mencionó anteriormente, se utilizan 2 funciones Lambda, los cuales se disparan al momento de entrar en los endpoints previamente mencionados. La estructura de los Lambda es la siguiente:

La función Lambda `authUser` posee el siguiente código:
```python
import json
import urllib3

def  lambda_handler(event, context):
	data = json.loads(event["body"])
	user = data["user"]
	passw = data["pass"]

	http = urllib3.PoolManager()
	url =  "http://172.31.25.86:5000/auth"

	r = http.request("POST", url, body=json.dumps({
		"user": user,
		"pass": passw
	}), headers={'Content-Type': 'application/json'})

	return {
	'statusCode': 200,
	'body': r.data
	}
```

La función Lambda `sendPartition` posee el siguiente código:
```python
import json
import urllib3

def  lambda_handler(event, context):
	http = urllib3.PoolManager()
	partitioner_location =  f"172.31.25.120:5000"
	auth_location =  f"172.31.25.86:5000"
	data = json.loads(event["body"])
	
	r = http.request("POST", f"http://{auth_location}/validate", headers={
		"Authorization": event["headers"]["authorization"],
		"Accept": "application/json",
		"Content-Type": "application/json"
	}, body=json.dumps({}))

	if r.status !=  200:
		return {
			'statusCode': r.status,
			'body': {"error": "Could not validate user"}
		}

	data["user"] = json.loads(r.data)["user"]
	
	req = http.request("POST", f"http://{partitioner_location}/routing", body=json.dumps(data), headers={
		"Accept": "application/json",
		"Content-Type": "application/json"
	})
	
	mom_location = json.loads(req.data)["node_location"]
	
	req_f = http.request("POST", f"http://{mom_location}/", body=json.dumps(data), headers={
	"Accept": "application/json",
	"Content-Type": "application/json"
	})

	return {
		'statusCode': 200,
		'body': req_f.data
	}
```
#### Grupos de seguridad
Todos las máquinas Y las funciones Lambda utilizan la misma VPC y grupos de seguridad para la conexión entre los componentes. Está configurado de la siguiente manera:
![Configuración de grupo de seguridad](https://i.imgur.com/NqkOHU4.png)

Este grupo de seguridad expone los puertos utilizados en los servidores para una lista de subredes internas específicas, compartiendo la misma zona de disponibilidad de las funciones Lambda

### Lanzar servidores
Los servidores se pueden lanzar con los archivos `.sh` dentro de la carpeta `/config`, estos crean y ejecutan automáticamente los archivos de Python correspondientes al servidor a ejecutar como un servicio en systemd; su estructura se explicó previamente en la sección de ejecución local.

Por ejemplo, para la ejecución del servicio de autenticación, basta con darle permisos de ejecución al archivo `auth.service`, de la siguiente manera:

    sudo chmod 777 auth.service
Para finalmente ejecutar el proceso de instalación en el archivo .sh

    sudo ./install_auth.sh

Cuando el script termine de ejecutarse, se puede ver el estado de la aplicación utilizando `systemctl status auth`, dando una respuesta similar a esta:

![Servicio de autenticación corriendo](https://i.imgur.com/EQDnTII.png)

El proceso es el mismo para todos los demás servidores con sus respectivos `.service` e `install_[service].sh`

#### Cliente y uso del software
Dentro del directorio`/client` del repositorio existe el archivo `main.py` junto con su archivo de configuración `config.json` (léase sección de ejecución local para su configuración básica) para establecer conexiones de manera básica.

En el mismo directorio, basta con ejecutar el archivo main de la siguiente forma: `python main.py`

Para realizar una petición de push a una cola con exchange `logs` y nombre de cola `warnings`, se puede utilizar el siguiente snippet como una prueba de conexión:

```python
import json, pathlib
import Connection

config = None # Archivo de configuración


def load_config():
	global config
    path = pathlib.Path("config.json")
    with open(f"{pathlib.Path.absolute(path)}", "r") as file:
        config = json.load(file) # Cargar configuración en JSON

def set_connection(type, exchange, routing_key):
    if type not in ["q", "t"]:
        return TypeError("Incorrect type specified")
    
    return Connection.Connection(type, exchange, routing_key, config)


if __name__ == "__main__":
	load_config()

    # Push Queue
    # Se autentica y crea la conexión a la API
    cn = set_connection("q", "logs", "info")
	# Publica "Mensaje1" en la cola
    cn.publish("Mensaje1", lambda x: print(f"Se envio, con respuesta: {x.json()}"))
	
```

Obteniendo una respuesta similar a esta:

![Respuesta de push](https://i.imgur.com/1HpOOzc.png)

Para consumir información de una cola, se debe utilizar el método `consume`, del mismo objeto de la conexión:

```python
cn.consume(lambda x: print(f"El mensaje recibido fue: {x.json()}"))
```

Con resultado:

![Resultado de pull](https://i.imgur.com/w5yoIfd.png)



## Referencias
1. _ActiveMQ con Message Oriented Middleware_. (s. f.). SG Buzz. https://sg.com.mx/revista/41/activemq-message-oriented-middleware
2. Kleppmann, M. (2017). _Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems_. «O’Reilly Media, Inc.»
3. _Partitioning and replication: benefits & challenges_. (s. f.). A Curious Mind. https://dimosr.github.io/partitioning-and-replication/
4. Kumili, L. (2024, 4 diciembre). The Power of Kafka Keys: Why Choosing the Right One Matters. _Medium_. https://medium.com/@leela.kumili/the-power-of-kafka-keys-why-choosing-the-right-one-matters-adbe80785dc5
