#! /usr/bin/env python3

"""
Command-line script to deploy a frontend app to s3.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import io
import subprocess
import sys
from functools import partial
from os import path

import click
import CloudFlare
import yaml

# Add top-level module path to sys.path before importing tubular code.
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from tubular.scripts.helpers import _log, _fail  # pylint: disable=wrong-import-position

SCRIPT_SHORTNAME = 'Deploy frontend'
LOG = partial(_log, SCRIPT_SHORTNAME)
FAIL = partial(_fail, SCRIPT_SHORTNAME)


@click.command()
@click.option(
    '--env-config-file',
    help='File from which to read environment configuration variables.',
)
@click.option(
    '--app-name',
    help='Name of the frontend app.',
)
@click.option(
    '--app-dist',
    help='Path to the frontend app dist directory.',
)
@click.option(
    '--purge-cache',
    default=False,
    is_flag=True,
    help='Boolean to decide if Cloudflare cache needs to be purged or not.',
)
def frontend_deploy(env_config_file, app_name, app_dist, purge_cache):
    """
    Copies a frontend application to an s3 bucket.

    Args:
        env_config_file (str): Path to a YAML file containing environment configuration variables.
        app_name (str): Name of the frontend app.
        app_dist (str): Path to frontend application dist directory.
        purge_cache (bool): Should Cloudflare cache needs to be purged.
    """
    if not env_config_file:
        FAIL(1, 'Environment config file was not specified.')
    if not app_name:
        FAIL(1, 'Frontend application name was not specified.')
    if not app_dist:
        FAIL(1, 'Frontend application dist path was not specified.')

    try:
        with io.open(env_config_file, 'r') as contents:
            env_vars = yaml.safe_load(contents)
    except IOError:
        FAIL(1, 'Environment config file {} could not be opened.'.format(env_config_file))

    bucket_name = env_vars.get('S3_BUCKET_NAME')
    if not bucket_name:
        FAIL(1, 'No S3 bucket name configured for {}.'.format(app_name))

    bucket_uri = 's3://{}'.format(bucket_name)

    proc = subprocess.Popen(
        ' '.join(['aws s3 sync', app_dist, bucket_uri, '--delete']),
        shell=True
    )
    return_code = proc.wait()
    if return_code != 0:
        FAIL(1, 'Could not sync app {} with S3 bucket {}.'.format(app_name, bucket_uri))

    if purge_cache:
        # Purge the Cloudflare cache for the frontend hostname.
        # Frontend S3 buckets are named by hostname.
        # Cloudflare zones are named by domain.
        # Assumes the caller's shell has the following environment
        # variables set to enable Cloudflare API auth:
        # CF_API_EMAIL
        # CF_API_KEY
        zone_name = '.'.join(bucket_name.split('.')[-2:])  # Zone name is the TLD
        data = {'hosts': [bucket_name]}
        cloudflare_client = CloudFlare.CloudFlare()
        try:
            zone_id = cloudflare_client.zones.get(params={'name': zone_name})[0]['id']  # pylint: disable=no-member
            cloudflare_client.zones.purge_cache.post(zone_id, data=data)  # pylint: disable=no-member
            LOG('Successfully purged Cloudflare cache for hostname {}.'.format(bucket_name))
        except (CloudFlare.exceptions.CloudFlareAPIError, IndexError, KeyError):
            FAIL(1, 'Failed to purge the Cloudflare cache for hostname {}.'.format(bucket_name))

    LOG('Frontend application {} successfully deployed to {}.'.format(app_name, bucket_name))


if __name__ == "__main__":
    frontend_deploy()  # pylint: disable=no-value-for-parameter
