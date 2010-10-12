from flaskext.script import Manager, Server, Shell
from statusboard.main import app, db

manager = Manager(app)
manager.add_command('runserver', Server())
manager.add_command('shell', Shell(make_context=lambda: dict(app=app, db=db)))

@manager.command
def syncdb():
    db.create_all()
    db.session.commit()

if __name__ == '__main__':
    manager.run()
