# :filename: translate.py

#import std libs
import os

# import 3rd parties libs
import click
from flask.cli import AppGroup

# import application libs


translate_cli = AppGroup('translate')

@translate_cli.command('init')
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel init -i messages.pot -d covid/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')
    
    
@translate_cli.command('update')
def update():
    """Update all languages."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d covid/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')

@translate_cli.command('compile')
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d covid/translations'):
        raise RuntimeError('compile command failed')
        
def init_app(app):
    app.cli.add_command(translate_cli)

