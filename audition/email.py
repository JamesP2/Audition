from audition import app, mail
from threading import Thread
from validate_email import validate_email


def send_mail_async(application, message):
    with application.app_context():
        mail.send(message)


def send_mail(message):
    if 'MAIL_ENABLE' not in app.config or not app.config['MAIL_ENABLE']:
        app.logger.info('Aborted email to %s (Subject: %s) as mail disabled', message.recipients, message.subject)
        return

    if 'MAIL_BCC' in app.config and app.config['MAIL_BCC'] is not None:
        if not validate_email(app.config['MAIL_BCC']):
            app.logger.error('BCC Email not valid: %s', app.config['MAIL_BCC'])

        else:
            message.bcc.append(app.config['MAIL_BCC'])

    mail_from = app.config['MAIL_FROM'][1] if type(app.config['MAIL_FROM']) == tuple else app.config['MAIL_FROM']

    if not validate_email(mail_from):
        app.logger.error('From Email not valid (%s). Aborting send', app.config['MAIL_FROM'])
        return

    message.sender = app.config['MAIL_FROM']

    app.logger.info('Sending email to %s (Subject: %s)', message.recipients, message.subject)

    thr = Thread(target=send_mail_async, args=[app, message])
    thr.start()
