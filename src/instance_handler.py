from src.chat_handler import ChatHandler

chat_handler = None

def init_chat_handler(sio, message_collection):
    global chat_handler
    if chat_handler is None:
        chat_handler = ChatHandler(sio, message_collection)
    return chat_handler

def get_chat_handler():
    return chat_handler