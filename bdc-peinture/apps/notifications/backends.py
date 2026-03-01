"""
Backends d'envoi de SMS — architecture pluggable via settings.SMS_BACKEND.
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod

import requests
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class BaseSmsBackend(ABC):
    """Interface commune pour tous les backends SMS."""

    @abstractmethod
    def send(self, telephone: str, message: str) -> bool:
        """
        Envoie un SMS.

        Args:
            telephone: Numéro de téléphone du destinataire.
            message: Contenu du SMS.

        Returns:
            True si envoyé avec succès.
        """


class LogSmsBackend(BaseSmsBackend):
    """Backend de développement — logge le SMS sans l'envoyer."""

    def send(self, telephone: str, message: str) -> bool:
        logger.info("SMS vers %s : %s", telephone, message)
        return True


class OvhSmsBackend(BaseSmsBackend):
    """Backend de production — envoie le SMS via l'API REST OVH."""

    def send(self, telephone: str, message: str) -> bool:
        application_key = settings.OVH_APPLICATION_KEY
        application_secret = settings.OVH_APPLICATION_SECRET
        consumer_key = settings.OVH_CONSUMER_KEY
        service_name = settings.OVH_SMS_SERVICE_NAME
        sender = getattr(settings, "OVH_SMS_SENDER", "")

        url = f"https://eu.api.ovh.com/1.0/sms/{service_name}/jobs"
        body = {
            "charset": "UTF-8",
            "receivers": [telephone],
            "message": message,
            "noStopClause": True,
            "priority": "high",
        }
        if sender:
            body["sender"] = sender

        timestamp = str(int(time.time()))
        # Signature OVH : SHA1($AS+"+"+$CK+"+"+$METHOD+"+"+$QUERY+"+"+$BODY+"+"+$TSTAMP)
        import json

        body_str = json.dumps(body)
        to_sign = f"{application_secret}+{consumer_key}+POST+{url}+{body_str}+{timestamp}"
        signature = "$1$" + hashlib.sha1(to_sign.encode("utf-8")).hexdigest()  # noqa: S324

        headers = {
            "Content-Type": "application/json",
            "X-Ovh-Application": application_key,
            "X-Ovh-Consumer": consumer_key,
            "X-Ovh-Timestamp": timestamp,
            "X-Ovh-Signature": signature,
        }

        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("SMS OVH envoyé à %s (service: %s)", telephone, service_name)
        return True


def get_sms_backend() -> BaseSmsBackend:
    """Charge dynamiquement le backend SMS depuis settings.SMS_BACKEND."""
    backend_path = getattr(settings, "SMS_BACKEND", "apps.notifications.backends.LogSmsBackend")
    backend_class = import_string(backend_path)
    return backend_class()
