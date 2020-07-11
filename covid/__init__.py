# :filename: covid/__init__.py

# std libs import
import os
import logging
from logging.handlers import RotatingFileHandler

# 3rd parties libs import
from flask import Flask, request, current_app
from flask_babel import Babel
from flask_babel import lazy_gettext as _l


babel = Babel()


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    babel.init_app(app)
    
    # START the configs valzer
    # load the default configuration file
    app.config.from_pyfile(os.path.join(app.instance_path, 'default_config.cfg'))
    if test_config is None:
        # when not testing, load the instance std config, this update the default values
        app.config.from_pyfile(os.path.join(app.instance_path, 'config.cfg'))
    else:
        # load the test config if passed in; see: setUp(self) in ../tests/unit_tests.py
        app.config.update(test_config)
    # END  the configs valzer

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #breakpoint()      #<
    # START setting logger
    if  not app.testing:
        if not os.path.exists(app.config['LOG']['DIR']):
            os.mkdir(app.config['LOG']['DIR'])
        file_handler = RotatingFileHandler(app.config['LOG']['FILE'], maxBytes=app.config['LOG']['BUFSIZE'],
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(app.config['LOG']['FILE_HANDLER_LEVEL'])
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(app.config['LOG']['APP_LOGGER_LEVEL'])
        app.logger.debug('Covid application starts')
    # END   setting logger

    # register the tranlate commands
    from . import cli
    cli.init_app(app)

    # register the dataframe
    from . import models
    models.init_app(app)
        
    from . import views
    app.register_blueprint(views.bp)
    #app.add_url_rule('/', endpoint='index')

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app


@babel.localeselector
def get_locale():
    #< to test Italian language: decomment the following and comment the final return
    #return 'it'
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])