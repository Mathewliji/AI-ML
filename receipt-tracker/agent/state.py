from typing import TypedDict, Literal, Optional


class AgentState(TypedDict):
    task: Literal["upload", "query"]
    image_b64: Optional[str]          # base64-encoded receipt image
    image_media_type: Optional[str]   # image/jpeg | image/png | image/webp
    receipt_data: Optional[dict]      # structured extraction from Claude Vision
    category: Optional[str]           # food | travel | shopping | utilities | healthcare | entertainment | other
    receipt_id: Optional[int]         # DB primary key after save
    user_message: Optional[str]       # natural-language query from the user
    response: Optional[str]           # final message shown in the chat UI
    error: Optional[str]
