from distutils.core import setup

setup(
    name='Audition',
    version='1.0',
    packages=['audition'],
    url='',
    license='',
    author='James Phillips',
    author_email='james@jp2.me.uk',
    description='Online Audition Management & Booking',
    requires=['flask', 'flask_login', 'flask_sqlalchemy', 'flask_migrate',
              'flask_script', 'flask_oauthlib', 'flask_markdown', 'flask_mail',
              'validate_email']
)
