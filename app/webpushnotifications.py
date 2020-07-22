from pywebpush import webpush
from app import app


def send_web_push(subscription_information, message_body):
    return webpush(
        subscription_info=subscription_information,
        data=message_body,
        vapid_private_key=app.config["VAPID_PRIVATE_KEY"],
        vapid_claims=app.config["VAPID_CLAIMS"]
    )