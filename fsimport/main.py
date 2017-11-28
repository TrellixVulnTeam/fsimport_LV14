from . import __version__

import click
import logging
import os
import shutil
import tempfile

from fsimport.archive import unarchive
from fsimport.config import load_config
from fsimport.rules import process_rules
from fsimport.source import get_source


logger = logging.getLogger(__name__)
tmp_directory = tempfile.mkdtemp()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('fsimport version {}'.format(__version__))
    ctx.exit()


# Ideas for extra-options:
#  - configure tmp_directory
#  - flag to create backup when updating files
# 

@click.command()
@click.option('--config', '-c', type=click.File(), help='configuration file')
@click.option('--dry-run', is_flag=True, help='predict changes without performing them')
@click.option('--extra-vars', '-e', multiple=True)
@click.option('--verbose', '-v', is_flag=True, default=False, help='be more verbose')
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True)
@click.argument('src')
def cli(config, dry_run, extra_vars, verbose, src):
    """fsimport - import files into directory using filesets"""
    logger.debug('config: {}'.format(config))
    logger.debug('dry-run: {}'.format(dry_run))
    logger.debug('verbose: {}'.format(verbose))
    logger.debug('extra-vars: {}'.format(extra_vars))

    # check source
    logger.info('Checking source')
    src = get_source(src)

    # load configuration
    logger.info('Loading configuration')
    config = load_config(config, extra_vars)
    environment_name = config.get('environment_name', None)
    if environment_name is None:
        logger.fatal('Incomplete configuration: environment_name not set')

    # add options to config
    config['dry_run'] = dry_run
    config['verbose'] = verbose

    try:
        # unarchiving package
        logger.info('Unarchiving {}'.format(src.name))
        package_files = unarchive(src.name, tmp_directory, environment_name)

        # process rules
        process_rules(config, tmp_directory, package_files)

    except Exception as e:
        logger.fatal(e)

    finally:    
        shutil.rmtree(tmp_directory)
        os.remove(src.name)


def main():
    cli()


if __name__ == '__main__':
    cli()
