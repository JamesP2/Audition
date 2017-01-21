from audition import app, mail
from threading import Thread


def send_mail_async(application, message):
    with application.app_context():
        mail.send(message)


def send_mail(message):
    if 'MAIL_BCC' in app.config and app.config['MAIL_BCC'] is not None:
        message.bcc.append(app.config['MAIL_BCC'])

    message.sender = app.config['MAIL_FROM']

    app.logger.info('Sending email to %s', message.recipients)

    thr = Thread(target=send_mail_async, args=[app, message])
    thr.start()
