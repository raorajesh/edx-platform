"""
Django Celery tasks for service status app
"""
import logging
from smtplib import SMTPException

from celery import task
from django.conf import settings
from django.core.mail import send_mail

ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
log = logging.getLogger(__name__)


@task(routing_key=ACE_ROUTING_KEY)
def send_verification_status_email(subject, message, from_addr, dest_addr):
    """
    Spins a task to send verification status email to the learner
    """
    try:
        send_mail(
            subject,
            message,
            from_addr,
            [dest_addr],
            fail_silently=False
        )
    except SMTPException:
        log.warning("Failure in sending verification status e-mail to %s", dest_addr)
