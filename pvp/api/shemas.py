from enum import Enum
from typing import Union, Literal
from ninja import Schema
from pydantic import Field


class MessageType(str, Enum):
    ANSWER = 'answer'
    RESULT = 'result'
    ENEMY_RESULT = 'enemy_result'


class MessageBase(Schema):
    type: MessageType
    task_index: int = Field(ge=0, description="Индекс задачи, начиная с 0")


class AnswerMessage(MessageBase):
    type: Literal[MessageType.ANSWER] = MessageType.ANSWER
    answer: str


class ResultMessage(MessageBase):
    type: Union[
        Literal[MessageType.RESULT],
        Literal[MessageType.ENEMY_RESULT]
    ]
    is_correct: bool


# Объединенная схема для всех типов сообщений
Message = Union[AnswerMessage, ResultMessage]
