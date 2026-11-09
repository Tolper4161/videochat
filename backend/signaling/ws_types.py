from enum import Enum


class WebSocketType(Enum):
    START_CALL = "start_call"
    JOIN = "join"
    LEAVE = "leave"
    END_CALL = "end_call"
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    MUTE_CHANGED = "mute_changed"
    CAMERA_CHANGED = "camera_changed"
    CONSUMER_TYPE = "consumer_type"
    ERROR = "error"
    EXCLUDED_PARTICIPANT_ID = "excluded_participant_id"
