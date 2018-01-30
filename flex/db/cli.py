import os
import argparse
from flex.core.cli import Manager, prompt_bool
from .utils import app_get_db_client
from flask import current_app
from .migrations import Config, migrations
from alembic import command



console = Manager(usage="Perform SQL database migrations and operations with SQLAlchemy.")


@console.command
def createdb(binds=None):
	"""Creates the configured database and tables from sqlalchemy models."""
	binds = () if binds is None else binds.split(',')
	_dbclient().create_database(*binds)


@console.command
def dropdb(binds=None):
	"""Drops the current sqlalchemy database."""
	binds = () if binds is None else binds.split(',')
	if prompt_bool("Sure you want to drop the database?"):
		_dbclient().drop_database(*binds)


# @console.command
# def recreatedb(create_tables=True, drop_tables=False):
# 	"""Recreates the database and tables (same as issuing 'drop_db' and then 'create_db')."""
# 	dropdb(drop_tables)
# 	createdb(create_tables)


# @console.command
# def createtables():
# 	"""Creates the configured database and tables from sqlalchemy models."""
# 	_dbclient().create_all()


@console.command
def droptables():
	"""Drops the current sqlalchemy database."""
	if prompt_bool("Sure you want to drop all tables in the database?"):
		_dbclient().drop_all()


# @console.command
# def recreatetables():
# 	"""Recreates database tables (same as issuing 'drop_tables' and then 'create_tables')."""
# 	droptables()
# 	createtables()


def _dbclient(app=None):
	return app_get_db_client(app or current_app)



@console.option('-d', '--directory', dest='directory', default=None,
	help="migration script directory (default is '.migrations')")
@console.option('--multidb', dest='multidb', action='store_true', default=False,
	help="Multiple databases migraton (default is False)")
def init(directory=None, multidb=False):
	"""Creates a new migration repository"""

	createdb()

	if directory is None:
		directory = migrations.directory
	config = Config()
	config.set_main_option('script_location', directory)
	config.config_file_name = os.path.join(directory, 'alembic.ini')
	config = migrations.migrate.call_configure_callbacks(config)
	if multidb:
		command.init(config, directory, 'flex-multidb')
	else:
		command.init(config, directory, 'flex')


@console.option('--rev-id', dest='rev_id', default=None,
	help=('Specify a hardcoded revision id instead of generating one'))
@console.option('--version-path', dest='version_path', default=None,
	help=('Specify specific path from config for version file'))
@console.option('--branch-label', dest='branch_label', default=None,
	help=('Specify a branch label to apply to the new revision'))
@console.option('--splice', dest='splice', action='store_true', default=False,
	help=('Allow a non-head revision as the "head" to splice onto'))
@console.option('--head', dest='head', default='head',
	help=('Specify head revision or <branchname>@head to base new revision on'))
@console.option('--sql', dest='sql', action='store_true', default=False,
	help=("Don't emit SQL to database - dump to standard output instead"))
@console.option('--autogenerate', dest='autogenerate', action='store_true', default=False,
	help=('Populate revision script with candidate migration operations, based on comparison of database to model'))
@console.option('-m', '--message', dest='message', default=None,
	help='Revision message')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def revision(directory=None, message=None, autogenerate=False, sql=False,
		head='head', splice=False, branch_label=None, version_path=None, rev_id=None):
	"""Create a new revision file."""
	config = migrations.migrate.get_config(directory)
	command.revision(config, message, autogenerate=autogenerate, sql=sql,
		head=head, splice=splice, branch_label=branch_label,
		version_path=version_path, rev_id=rev_id
	)



@console.option('--rev-id', dest='rev_id', default=None,
	help=('Specify a hardcoded revision id instead of generating one'))
@console.option('--version-path', dest='version_path', default=None,
	help=('Specify specific path from config for version file'))
@console.option('--branch-label', dest='branch_label', default=None,
	help=('Specify a branch label to apply to the new revision'))
@console.option('--splice', dest='splice', action='store_true', default=False,
	help=('Allow a non-head revision as the "head" to splice onto'))
@console.option('--head', dest='head', default='head',
	help=('Specify head revision or <branchname>@head to base new revision on'))
@console.option('--sql', dest='sql', action='store_true', default=False,
	help=("Don't emit SQL to database - dump to standard output instead"))
@console.option('-m', '--message', dest='message', default=None)
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def migrate(directory=None, message=None, sql=False, head='head', splice=False,
		branch_label=None, version_path=None, rev_id=None):
	"""Alias for 'revision --autogenerate'"""
	config = migrations.migrate.get_config(directory, opts=['autogenerate'])
	command.revision(config, message, autogenerate=True, sql=sql,
			head=head, splice=splice, branch_label=branch_label,
			version_path=version_path, rev_id=rev_id
		)



@console.option('revision', nargs='?', default='head', help="revision identifier")
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def edit(directory=None, revision='current'):
	"""Edit current revision."""
	config = migrations.migrate.get_config(directory)
	command.edit(config, revision)



@console.option('--rev-id', dest='rev_id', default=None,
	help=('Specify a hardcoded revision id instead of generating one'))
@console.option('--branch-label', dest='branch_label', default=None,
	help=('Specify a branch label to apply to the new revision'))
@console.option('-m', '--message', dest='message', default=None)
@console.option('revisions', nargs='+',
	help='one or more revisions, or "heads" for all heads')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def merge(directory=None, revisions='', message=None, branch_label=None, rev_id=None):
	"""Merge two revisions together.  Creates a new migration file"""
	config = migrations.migrate.get_config(directory)
	command.merge(config, revisions, message=message, branch_label=branch_label, rev_id=rev_id)




@console.option('--tag', dest='tag', default=None,
	help=("Arbitrary 'tag' name - can be used by custom env.py scripts"))
@console.option('--sql', dest='sql', action='store_true', default=False,
	help=("Don't emit SQL to database - dump to standard output instead"))
@console.option('revision', nargs='?', default='head',
	help="revision identifier")
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
@console.option('-x', '--x-arg', dest='x_arg', default=None, action='append',
	help=("Additional arguments consumed by custom env.py scripts"))
def upgrade(directory=None, revision='head', sql=False, tag=None, x_arg=None):
		"""Upgrade to a later version"""
		config = migrations.migrate.get_config(directory, x_arg=x_arg)
		command.upgrade(config, revision, sql=sql, tag=tag)




@console.option('--tag', dest='tag', default=None,
	help=("Arbitrary 'tag' name - can be used by custom env.py scripts"))
@console.option('--sql', dest='sql', action='store_true', default=False,
	help=("Don't emit SQL to database - dump to standard output instead"))
@console.option('revision', nargs='?', default="-1",
	help="revision identifier")
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
@console.option('-x', '--x-arg', dest='x_arg', default=None, action='append',
	help=("Additional arguments consumed by custom env.py scripts"))
def downgrade(directory=None, revision='-1', sql=False, tag=None, x_arg=None):
	"""Revert to a previous version"""
	config = migrations.migrate.get_config(directory, x_arg=x_arg)
	if sql and revision == '-1':
		revision = 'head:-1'
	command.downgrade(config, revision, sql=sql, tag=tag)



@console.option('revision', nargs='?', default="head",
	help="revision identifier")
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def show(directory=None, revision='head'):
	"""Show the revision denoted by the given symbol."""
	config = migrations.migrate.get_config(directory)
	command.show(config, revision)




@console.option('-v', '--verbose', dest='verbose', action='store_true',
	default=False, help='Use more verbose output')
@console.option('-r', '--rev-range', dest='rev_range', default=None,
	help='Specify a revision range; format is [start]:[end]')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def history(directory=None, rev_range=None, verbose=False):
	"""List changeset scripts in chronological order."""
	config = migrations.migrate.get_config(directory)
	command.history(config, rev_range, verbose=verbose)




@console.option('--resolve-dependencies', dest='resolve_dependencies',
	action='store_true', default=False,
	help='Treat dependency versions as down revisions')
@console.option('-v', '--verbose', dest='verbose', action='store_true',
	default=False, help='Use more verbose output')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def heads(directory=None, verbose=False, resolve_dependencies=False):
	"""Show current available heads in the script directory"""
	config = migrations.migrate.get_config(directory)
	command.heads(config, verbose=verbose, resolve_dependencies=resolve_dependencies)




@console.option('-v', '--verbose', dest='verbose', action='store_true',
	default=False, help='Use more verbose output')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def branches(directory=None, verbose=False):
	"""Show current branch points"""
	config = migrations.migrate.get_config(directory)
	command.branches(config, verbose=verbose)



@console.option('--head-only', dest='head_only', action='store_true', default=False,
	help='Deprecated. Use --verbose for additional output')
@console.option('-v', '--verbose', dest='verbose', action='store_true',
	default=False, help='Use more verbose output')
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def current(directory=None, verbose=False, head_only=False):
	"""Display the current revision for each database."""
	config = migrations.migrate.get_config(directory)
	command.current(config, verbose=verbose, head_only=head_only)



@console.option('--tag', dest='tag', default=None,
	help=("Arbitrary 'tag' name - can be used by custom env.py scripts"))
@console.option('--sql', dest='sql', action='store_true', default=False,
	help=("Don't emit SQL to database - dump to standard output instead"))
@console.option('revision', default=None, help="revision identifier")
@console.option('-d', '--directory', dest='directory', default=None,
	help=("migration script directory (default is 'migrations')"))
def stamp(directory=None, revision='head', sql=False, tag=None):
	"""'stamp' the revision table with the given revision; don't run any
	migrations"""
	config = migrations.migrate.get_config(directory)
	command.stamp(config, revision, sql=sql, tag=tag)
