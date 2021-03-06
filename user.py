#!/usr/bin/env python3
import os, sys, logging
import arrow, bcrypt, click, json, xkcdpass
from xkcdpass import xkcd_password as xkcdpass

DEBUG = True if os.environ.get('DEBUG') is not None else False

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG if DEBUG else logging.ERROR)
logger = logging.getLogger()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR') or '/var/lib/dav/data'
logger.debug('BASE_DIR: %s', BASE_DIR)
logger.debug('DATA_DIR: %s', DATA_DIR)

DATASTORE = os.path.abspath(os.path.join(BASE_DIR, os.environ.get('DATASTORE') or '/user.json'))
ARCHIVE_DIR = os.path.join(DATA_DIR, '_archive/')
logger.debug('DATASTORE: %s', DATASTORE)
logger.debug('ARCHIVE_DIR: %s', ARCHIVE_DIR)

PASSWD = os.environ.get('PASSWD_FILE') or '/user.passwd'
logger.debug('PASSWD: %s', PASSWD)


class XKCD():

    def __init__(self):
        self.words = xkcdpass.generate_wordlist(wordfile=xkcdpass.locate_wordfile(), min_length=5, max_length=10)

    def generate(self):
        return xkcdpass.generate_xkcdpassword(self.words, numwords=3, delimiter='-')


def _load_datastore():
    logger.debug('Loading datastore.')
    try:
        with open(DATASTORE, 'r') as f:
            logger.debug('Loading datastore from %s', DATASTORE)
            return json.load(f)
    except Exception as e:
        logger.info('Failed to load datastore at %s', DATASTORE)
        raise e


def _save_datastore(ds):
    logger.debug('Saving datastore.')
    try:
        with open(DATASTORE, 'w') as f:
            json.dump(ds, f)
    except Exception as e:
        logger.error('Failed to write datastore at %s', DATASTORE)


def _hash_password(password):
  hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()
  return '$2y$' + hash[4:]


@click.group()
def cli():
  pass


@cli.command()
def passwd():
  """Generate user.passwd file."""
  logger.info('Generating user.passwd')
  ds = _load_datastore()

  for name, data in ds['users'].items():
      if data['active'] is True:
          click.echo('{}:{}'.format(name, data['passwd']))


@cli.command()
def sql():
    """Generate SQL."""
    logger.info('Generating SQL-file')
    ds = _load_datastore()

    for name, data in ds['users'].items():
        if data['active'] is True:
            click.echo("""CREATE DATABASE IF NOT EXISTS {db};
                          CREATE USER IF NOT EXISTS '{user}'@'{host}' IDENTIFIED WITH bcrypt USING '{hash}';
                          GRANT ALL PRIVILEGES on {db}.* to '{user}'@'{host}';""".format(user=name,
                                                                                         hash=data['passwd'],
                                                                                         db=name,
                                                                                         host='%'))
    click.echo("FLUSH PRIVILEGES;")

@cli.command()
@click.argument('names', nargs=-1)  # Allow unlimited number of usernames
def add(names):
    """Add new user."""
    xkcd = XKCD()

    ds = _load_datastore()

    logger.debug('%s', names)

    for name in names:
        password = xkcd.generate()

        ds['users'][name] = {'passwd': _hash_password(password),
                             'active': True,
                             'timestamp': arrow.utcnow().timestamp}

        click.echo('{};{}'.format(name, password))

        logger.debug('DATA_DIR %s', DATA_DIR)
        dir = os.path.join(DATA_DIR, '{}/'.format(name))
        logger.debug('USER_DIR for new user: %s', dir)
        try:
            os.makedirs(dir)
            logger.info('Directory created %s', dir)
        except FileExistsError as e:
            logger.info('Directory for user %s already exists.', name)
        except PermissionError as e:
            logger.error('Permission denied for data dir (%s)', DATA_DIR)

    _save_datastore(ds)


@cli.command()
@click.argument('names', nargs=-1)
def remove(names):
    """Move existing user to archive directory."""
    try:
        os.mkdir(ARCHIVE_DIR)
        logger.info('Creating archive directory, %s', ARCHIVE_DIR)
    except FileExistsError as e:
        pass

    ds = _load_datastore()

    for name in names:
        if not name in ds['users']:
            logger.error('User %s not found.', name)
        try:
            logger.info('Moving directory for %s to archive.', name)
            src = os.path.join(DATA_DIR, '{}/'.format(name))
            dst = os.path.join(ARCHIVE_DIR, '{}/'.format(name))
            os.rename(src, dst)
            ds
        except Exception as e:
            logger.error('Failure!', exc_info=True)


if __name__ == '__main__':
  cli()
