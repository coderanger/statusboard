from flaskext.script import Manager, Server, Shell
from flaskext.celery import install_commands as install_celery_commands
from statusboard.main import app, db

manager = Manager(app)
manager.add_command('runserver', Server())
manager.add_command('shell', Shell(make_context=lambda: dict(app=app, db=db)))
install_celery_commands(manager)

@manager.command
def syncdb():
    db.create_all()
    db.session.commit()

if __name__ == '__main__':
    manager.run()
