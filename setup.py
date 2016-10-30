from distutils.core import setup

setup(
    name='audition',
    version='',
    packages=['audition'],
    url='',
    license='',
    author='James Phillips',
    author_email='james@jp2.me.uk',
    include_package_data=True,
    description='Audition Management', requires=['flask', 'flask_login', 'flask_sqlalchemy']
)
