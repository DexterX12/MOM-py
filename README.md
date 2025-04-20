# Message-Oriented Middleware
Este middleware está diseñado para la comunicación  y transferencia de mensajes entre clientes, aplicando principios de sistemas distribuidos.
## Análisis y requerimientos iniciales
El foco de este trabajo se centra en la implementación de un servicio de mensajería similar a servicios como *Apache Kafka* y *RabbitMQ*, con un enfoque en la **Tolerancia a fallos**, concepto comúnmente trabajado en sistemas distribuidos.
Los requerimientos funcionales iniciales consisten en garantizar la comunicación de varios clientes a través de colas y tópicos.

![Flujo básico de comunicación en MOMs](https://i.imgur.com/rTS0IbU.png)

*Flujo básico de comunicación en MOMs**¹***

Además, para asegurarse de que la comunicación solo se realiza entre usuarios autorizados, el servicio debe implementar algún tipo de autenticación.
Finalmente, respecto al aspecto no funcional, se debe implementar mecanismos para garantizar la tolerancia a fallos, mecanismos presentes en sistemas distribuidos como la ***replicación y particionamiento*** de los datos, además de la forma en como estos son replicados y particionados.

En la siguiente sección se presentará las decisiones tomadas para un acercamiento a la implementación de estos requerimientos.
## Diseño y elección de patrones
Respecto a la parte funcional, se tomaron en cuenta los siguientes aspectos:
#### Mensajería, colas y tópicos
* Los mensajes son identificados mediante una llave o "routing key", permitiendo el enrutamiento de estos a sus correspondientes colas/tópicos.
* Cada instancia de MOM posee una lista de usuarios "suscritos" a un tópico, creando una cola especial para cada usuario suscrito. Esto a su vez utiliza el ***mecanismo de pull***, donde cada cliente es responsable de verificar la existencia de nuevos mensajes en el tiempo.
#### Autenticación
* El ingreso de usuarios nuevos a la base de datos es manual, por lo que no se ha implementado un frontend que permita el registro de usuarios.
* Cualquier acción dentro de cada servicio de MOM requiere autenticación a partir de **tokens**, utilizando JWT, el cual es *stateless*.
* Cada usuario que inicie sesión, es asignado un token de duración temporal (1 hora por defecto), donde puede realizar acciones de productor y suscriptor a través de dicho token.

Respecto a la parte no funcional y temas de arquitectura, se tiene lo siguiente:
#### Arquitectura y Detalles
El servicio está desarrollado en su totalidad en Python, utilizando gRPC como protocolo de comunicación entre los nodos de servicio de MOM, además de la comunicación a través de API REST entre cliente-MOM. Esta arquitectura se orquestó con el concepto de ***tolerancia a fallos*** en mente, donde se establece un servicio de particionamiento para asignar los mensajes a partir de sus identificadores a los nodos correspondientes y, un servicio de replicación en cada nodo MOM para garantizar la redundancia y consistencia de los datos.

![Arquitectura principal](https://i.imgur.com/g7F7KbH.png)

*Arquitectura principal del servicio*

Las peticiones que los clientes realizan para suscribirse o publicar en algún tópico o cola son redireccionados a través de la API Gateway, de AWS, utilizando una función Lambda, también, de AWS. La necesidad del redireccionamiento proviene del principio de particionamiento; es necesario llevar el mensaje que el cliente necesita entregar a la cola o tópico correspondiente, sin importar en el nodo en que se encuentre, y este proceso debe ser transparente para el usuario. Por esta razón, se aplicó la siguiente arquitectura de localización de la información:

![Localización de la información](https://i.imgur.com/OCggPAx.png)

*Enrutamiento de la información²*

En el caso de este proyecto, el routing tier es la API Gateway, la cual a través de una función Lambda, le pregunta al servicio de particionamiento (que funciona en el nodo como un servicio junto a ZooKeeper), que nodo le pertenece la *routing key* del mensaje entrante, para luego devolver la dirección del MOM y reenviar la petición. Finalmente, la respuesta es devuelta al cliente que originalmente inició la petición.

Para mantener control de qué nodos existen y cuáles son lideres de cada partición para garantizar el correcto orden de replicación, se utiliza Apache ZooKeeper, el cual posee una estructura inspirada en sistemas de archivos, lo que permite guardar de manera estructurada la información de los nodos que hagan parte del servicio, además de la capacidad de obtener cambios en la topología, y algoritmos de elección de lider.

![Estructura de control](https://i.imgur.com/kebebLU.png)

*Control de nodos MOM mediante ZooKeeper*

Cada uno de los nodos le ofrece a ZooKeeper la metadata relevante para la comunicación de mensajes, así como para temas de particionamiento y replicación.
