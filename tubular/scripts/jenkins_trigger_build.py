#! /usr/bin/env python3

"""
Command-line script to trigger a jenkins job
"""
from __future__ import absolute_import
import logging
from os import path
import sys

import click
from jenkinsapi.constants import STATUS_FAIL, STATUS_ERROR, STATUS_ABORTED, STATUS_REGRESSION, STATUS_SUCCESS

# Add top-level module path to sys.path before importing tubular code.
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from tubular import jenkins  # pylint: disable=wrong-import-position


@click.command()
@click.option(
    u"--url",
    help=u"The base jenkins URL. E.g. https://test-jenkins.testeng.edx.org",
    type=str,
    required=True,
    default=u"https://test-jenkins.testeng.edx.org"
)
@click.option(
    u"--user_name",
    help=u"The Jenkins username for triggering the job.",
    type=str,
    required=True,
)
@click.option(
    u"--user_token",
    help=u"API token for the user. Available at {url}/user/{user_name)/configure",
    type=str,
    required=True,
    envvar=u'JENKINS_USER_TOKEN'
)
@click.option(
    u"--job",
    help=u"The name of the jenkins job. E.g. test-project",
    type=str,
    required=True,
)
@click.option(
    u"--token",
    help=u"The authorization token for the job. Must match that configured in the job definition.",
    type=str,
    required=True,
    envvar=u'JENKINS_JOB_TOKEN'
)
@click.option(
    u"--cause",
    help=u"Text that will be included in the recorded build cause.",
    type=str,
    required=False,
)
@click.option(
    u"--param",
    help=u"Key/value pairs to pass to the job as parameters. E.g. --param FOO bar --param BAZ biz",
    multiple=True,
    required=False,
    type=(str, str)
)
@click.option(
    u"--timeout",
    help=u"Maximum duration to wait for the jenkins job to complete (measured from "
         u"the time the job is triggered), in seconds.",
    type=float,
    required=False,
    default=30 * 60,
)
@click.option(
    u"--expected-status",
    help=u"The expected job status once the job completes.",
    default=STATUS_SUCCESS,
    type=click.Choice([
        STATUS_FAIL,
        STATUS_ERROR,
        STATUS_ABORTED,
        STATUS_REGRESSION,
        STATUS_SUCCESS,
    ])
)
def trigger(url, user_name, user_token, job, token, cause, param, timeout, expected_status):
    u"""Trigger a jenkins job. """
    status = jenkins.trigger_build(url, user_name, user_token, job, token, cause, param, timeout)
    return status == expected_status

if __name__ == u"__main__":
    # Configure logging for the tubular module methods to
    # print to stdout of the console that called this script.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    trigger()  # pylint: disable=no-value-for-parameter