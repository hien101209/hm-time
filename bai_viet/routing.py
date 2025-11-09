# bai_viet/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # personal chat: ws/chat/user_<userId>/
    re_path(r"ws/chat/user_(?P<user_id>\d+)/$", consumers.PersonalChatConsumer.as_asgi()),
    # group chat: ws/chat/group_<groupId>/
    re_path(r"ws/chat/group_(?P<group_id>\d+)/$", consumers.GroupChatConsumer.as_asgi()),
]
