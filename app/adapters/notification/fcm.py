"""Firebase Cloud Messaging adapter."""

import httpx
from typing import List, Dict, Any

from app.config import settings
from app.adapters.notification.base import NotificationProvider


class FCMProvider(NotificationProvider):
    """FCM push notification provider."""
    
    def __init__(self):
        self.server_key = settings.fcm_server_key
        self.base_url = "https://fcm.googleapis.com/fcm/send"
    
    async def send_push(
        self, 
        device_tokens: List[str], 
        title: str, 
        body: str,
        data: Dict[str, Any] = None
    ) -> bool:
        """Send push notification via FCM."""
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "registration_ids": device_tokens,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default"
            },
            "data": data or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers=headers
            )
            
            return response.status_code == 200
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """FCM doesn't handle emails."""
        raise NotImplementedError("Use email provider for emails")
    
    async def send_sms(self, to: str, message: str) -> bool:
        """FCM doesn't handle SMS."""
        raise NotImplementedError("Use SMS provider for SMS")