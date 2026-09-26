"""Universal Notification Dispatcher for Oil Trading Bot.
Supports:
1. ntfy.sh (Zero-signup, instant private phone push notifications)
2. Telegram Bot (Your own private, personal bot via @BotFather)
3. WhatsApp via Official Twilio Sandbox (+1 415 523 8886)
4. WhatsApp via CallMeBot
"""
import os
import urllib.parse
import requests
from typing import Optional


class UniversalNotifier:
    def __init__(
        self,
        # ntfy.sh (Easiest & 100% private)
        ntfy_topic: Optional[str] = None,
        # Telegram Bot
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        # WhatsApp (Twilio / CallMeBot)
        whatsapp_phone: Optional[str] = None,
        callmebot_api_key: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_from_number: str = "whatsapp:+14155238886"
    ):
        self.ntfy_topic = ntfy_topic or os.getenv("NTFY_TOPIC", "")
        self.telegram_bot_token = telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        
        self.whatsapp_phone = whatsapp_phone or os.getenv("WHATSAPP_PHONE", "")
        self.callmebot_api_key = callmebot_api_key or os.getenv("CALLMEBOT_API_KEY", "")
        self.twilio_account_sid = twilio_account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = twilio_auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = twilio_from_number

    def send_message(self, message: str, title: str = "🛢️ Oil Bot Alert", priority: str = "high") -> bool:
        """Send message through all configured private channels."""
        delivered = False

        # Channel 1: ntfy.sh (Instant private phone push)
        if self.ntfy_topic:
            if self._send_via_ntfy(message, title, priority):
                delivered = True

        # Channel 2: Telegram Bot
        if self.telegram_bot_token and self.telegram_chat_id:
            if self._send_via_telegram(message):
                delivered = True

        # Channel 3: Twilio Official WhatsApp
        if self.twilio_account_sid and self.twilio_auth_token and self.whatsapp_phone:
            if self._send_via_twilio(message):
                delivered = True

        # Channel 4: CallMeBot (only if explicitly set)
        if self.callmebot_api_key and self.whatsapp_phone:
            if self._send_via_callmebot(message):
                delivered = True

        if not delivered:
            print("\n[Alert Output - Configure NTFY_TOPIC or TELEGRAM to receive on phone]:")
            print(f"--- {title} ---")
            print(message)
            print("-" * 40 + "\n")

        return delivered

    def _send_via_ntfy(self, message: str, title: str, priority: str) -> bool:
        """Send instant push notification via ntfy.sh to your phone app."""
        try:
            url = f"https://ntfy.sh/{self.ntfy_topic}"
            headers = {
                "Title": title.encode("utf-8"),
                "Priority": priority,
                "Tags": "oil_drum,chart_with_upwards_trend"
            }
            res = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"[✓] Push notification sent to your phone via ntfy topic: '{self.ntfy_topic}'")
                return True
            else:
                print(f"[✗] ntfy error ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            print(f"[✗] Failed to send via ntfy: {e}")
            return False

    def _send_via_telegram(self, message: str) -> bool:
        """Send message via your private Telegram bot."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print("[✓] Telegram notification delivered to your private chat.")
                return True
            else:
                print(f"[✗] Telegram error ({res.status_code}): {res.text}")
                return False
        except Exception as e:
            print(f"[✗] Failed to send via Telegram: {e}")
            return False

    def _send_via_twilio(self, message: str) -> bool:
        """Send WhatsApp message using Twilio REST API."""
        try:
            to_phone = self.whatsapp_phone if self.whatsapp_phone.startswith("whatsapp:") else f"whatsapp:{self.whatsapp_phone}"
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            data = {"From": self.twilio_from_number, "To": to_phone, "Body": message}
            res = requests.post(url, data=data, auth=(self.twilio_account_sid, self.twilio_auth_token), timeout=15)
            if res.status_code in [200, 201]:
                print(f"[✓] WhatsApp notification delivered via Twilio.")
                return True
            return False
        except Exception as e:
            print(f"[✗] Twilio error: {e}")
            return False

    def _send_via_callmebot(self, message: str) -> bool:
        """Send via CallMeBot."""
        try:
            clean_phone = self.whatsapp_phone.replace("+", "").replace(" ", "").replace("-", "")
            encoded_text = urllib.parse.quote(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={self.callmebot_api_key}"
            res = requests.get(url, timeout=15)
            return res.status_code == 200
        except Exception:
            return False

    def send_trade_signal(
        self,
        symbol: str,
        action: str,
        price: float,
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
        catalyst: Optional[str] = None,
        tech_reason: Optional[str] = None
    ) -> bool:
        icon = "🟢" if action == "BUY" else "🛑" if action in ["EXIT", "STOP_LOSS"] else "🎯"
        title = f"{icon} OIL BOT: {action} {symbol} @ ${price:.2f}"
        
        lines = [
            f"*{action}*: *{symbol}*",
            f"💵 *Execution Price*: ${price:.2f}",
        ]
        if stop_loss:
            lines.append(f"🛑 *Stop Loss*: ${stop_loss:.2f}")
        if target:
            lines.append(f"🎯 *Take Profit*: ${target:.2f}")
        if catalyst:
            lines.append(f"📰 *News Catalyst*: {catalyst}")
        if tech_reason:
            lines.append(f"📈 *Technical*: {tech_reason}")
        lines.append("📱 *Revolut*: Ready to trade.")

        msg = "\n".join(lines)
        return self.send_message(msg, title=title)
