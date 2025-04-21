from concurrent import futures
from . import replicator_pb2
from . import replicator_pb2_grpc
import grpc

        # response = requests.post(self.location, json={
        #     "operation": "subscribe",
        #     "type": self.type,
        #     "data": {
        #         "headers": {
        #             "exchange": self.exchange,
        #             "routing_key": self.routing_key,
        #             "message_date": None
        #         },
        #         "body": None
        #     }
        # }

class ReplicateServicer(replicator_pb2_grpc.ReplicateServicer):
    def PopulateReplication(self, request, context):
        # Request is the object which has all the key:value pairs
        print(request)
        print(request.body) # For example, you can access the message's body like this
        response = request.post("127.0.0.1:5000", json={
            "operation": request.operation,
            "type": request.type,
            "data": {
                "headers": {
                    "exchange": request.exchange,
                    "routing_key": request.routing_key,
                    "message_date": request.message_date
                },
                "body": request.body
            }
        })
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