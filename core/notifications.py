import logging

logger = logging.getLogger(__name__)


def send_whatsapp_code(whatsapp: str, code: str) -> None:
    """
    Envia código de verificação via WhatsApp.

    TODO(notifications): plugar provedor real via settings — ex:
      Z-API:   POST settings.zapi_url  body={"phone": whatsapp, "message": f"Seu código CCI: {code}"}
      Twilio:  client.messages.create(to=f"whatsapp:{whatsapp}", from_=settings.twilio_from, body=...)
    Por enquanto loga em INFO para facilitar testes locais.
    """
    logger.info("whatsapp_code_simulated whatsapp=%s code=%s", whatsapp, code)
