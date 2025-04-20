from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class MessageMOM(_message.Message):
    __slots__ = ("operation", "type", "exchange", "routing_key", "message_date", "body")
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    EXCHANGE_FIELD_NUMBER: _ClassVar[int]
    ROUTING_KEY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_DATE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    operation: str
    type: str
    exchange: str
    routing_key: str
    message_date: int
    body: str
    def __init__(self, operation: _Optional[str] = ..., type: _Optional[str] = ..., exchange: _Optional[str] = ..., routing_key: _Optional[str] = ..., message_date: _Optional[int] = ..., body: _Optional[str] = ...) -> None: ...

class ReplicationSuccess(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
