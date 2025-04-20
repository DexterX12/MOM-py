from concurrent import futures
import replicator_pb2
import replicator_pb2_grpc
import grpc

class ReplicateServicer(replicator_pb2_grpc.ReplicateServicer):
    def PopulateReplication(self, request, context):
        # Request is the object which has all the key:value pairs
        print(request)
        print(request.body) # For example, you can access the message's body like this
        return replicator_pb2.ReplicationSuccess(success=True)


# Initialize this file as a separate service, so it's listening any requests for 
# replicating messages
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replicator_pb2_grpc.add_ReplicateServicer_to_server(ReplicateServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()