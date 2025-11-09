# bai_viet/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import TinNhan, NhomChat

User = get_user_model()

def chat_group_name_for_users(user1_id, user2_id):
    # consistent channel name
    a, b = sorted([str(user1_id), str(user2_id)])
    return f"personal_chat_{a}_{b}"

class PersonalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.user = self.scope["user"]

        # verify other exists
        try:
            self.other_user = await database_sync_to_async(User.objects.get)(id=self.other_user_id)
        except User.DoesNotExist:
            await self.close()
            return

        self.room_group_name = chat_group_name_for_users(self.user.id, self.other_user.id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # notify presence: user online in this chat
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "user_presence", "user_id": self.user.id, "status": "online"}
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "user_presence", "user_id": self.user.id, "status": "offline"}
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "send_message":
            content = data.get("content", "").strip()
            reply_to = data.get("reply_to")
            attachment = data.get("attachment")  # for simplicity: handle attachments via normal POST
            tn = await self.create_message(content, reply_to, attachment)
            payload = {
                "action": "new_message",
                "message": self.message_to_json(tn)
            }
            await self.channel_layer.group_send(self.room_group_name, {"type": "chat.message", "text": json.dumps(payload)})

        elif action == "typing":
            await self.channel_layer.group_send(self.room_group_name, {"type": "typing", "user_id": self.user.id})

        elif action == "mark_read":
            # mark all messages from other_user to me as read
            await self.mark_read()

        elif action == "react":
            message_id = data.get("message_id")
            emoji = data.get("emoji")
            await self.react(message_id, emoji)

    async def chat_message(self, event):
        await self.send(text_data=event["text"])

    async def typing(self, event):
        await self.send(text_data=json.dumps({"action": "typing", "user_id": event["user_id"]}))

    async def user_presence(self, event):
        await self.send(text_data=json.dumps({"action": "presence", "user_id": event["user_id"], "status": event["status"]}))

    @database_sync_to_async
    def create_message(self, content, reply_to, attachment):
        print("Create")
        tn = TinNhan.objects.create(
            nguoi_gui=self.user,
            nguoi_nhan=self.other_user,
            noi_dung=content,
            # attachment empty here; prefer uploading via HTTP and send via message ID
        )
        if reply_to:
            try:
                tn.reply_to = TinNhan.objects.get(id=reply_to)
                tn.save()
            except TinNhan.DoesNotExist:
                pass
        return tn

    @database_sync_to_async
    def mark_read(self):
        TinNhan.objects.filter(nguoi_gui=self.other_user, nguoi_nhan=self.user, is_read=False).update(is_read=True)

    @database_sync_to_async
    def react(self, message_id, emoji):
        try:
            m = TinNhan.objects.get(id=message_id)
            reactions = m.reactions or {}
            user_id = str(self.user.id)
            reactions[user_id] = emoji
            m.reactions = reactions
            m.save()
            return m
        except TinNhan.DoesNotExist:
            return None

    def message_to_json(self, tn):
        print("to  json ")
        return {
            "id": tn.id,
            "sender_id": tn.nguoi_gui.id,
            "sender_username": tn.nguoi_gui.username,
            "content": tn.noi_dung,
            "attachment_url": tn.attachment.url if tn.attachment else None,
            "thoi_gian": tn.thoi_gian.isoformat(),
            "is_read": tn.is_read,
            "reply_to": tn.reply_to.id if tn.reply_to else None,
            "reactions": tn.reactions or {},
        }

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        try:
            self.nhom = await database_sync_to_async(NhomChat.objects.get)(id=self.group_id)
        except NhomChat.DoesNotExist:
            await self.close(); return

        # verify membership
        is_member = await database_sync_to_async(self.nhom.thanh_vien.filter(id=self.user.id).exists)()
        if not is_member:
            await self.close(); return

        self.room_group_name = f"group_chat_{self.group_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get("action")
        if action == "send_message":
            content = data.get("content", "").strip()
            tn = await self.create_group_message(content)
            payload = {"action": "new_message", "message": self.message_to_json(tn)}
            await self.channel_layer.group_send(self.room_group_name, {"type": "group.message", "text": json.dumps(payload)})

    async def group_message(self, event):
        await self.send(text_data=event["text"])

    @database_sync_to_async
    def create_group_message(self, content):
        return TinNhan.objects.create(nguoi_gui=self.user, nhom=self.nhom, noi_dung=content)

    def message_to_json(self, tn):
        print("to - json 2 ")
        return {
            "id": tn.id,
            "sender_id": tn.nguoi_gui.id,
            "sender_username": tn.nguoi_gui.username,
            "content": tn.noi_dung,
            "thoi_gian": tn.thoi_gian.isoformat(),
            "attachment_url": tn.attachment.url if tn.attachment else None,
            "reactions": tn.reactions or {},
        }
