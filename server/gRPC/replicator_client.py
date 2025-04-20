import replicator_pb2
import replicator_pb2_grpc
import grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = replicator_pb2_grpc.ReplicateStub(channel)
    # Update this
    # This client needs to send the incoming messages from this MOM to the other MOMs connected
    # The definition of a single message can be seen in the protofile replicator.proto
    # This is an example on how a client can send a defined message, in this case
    # it needs to be replaced with the incoming message from the client for it to be
    # replicated
    response = stub.PopulateReplication(replicator_pb2.MessageMOM(
        body="Esto es un mensaje",
        exchange="mensajes",
        routing_key="chat",
        type="q",
        operation="push",

    ))
    print(response)