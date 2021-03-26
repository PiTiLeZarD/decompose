#!/usr/bin/env python
# Author: Jonathan Adami (pitilezard@gmail.com)
# Source: https://github.com/PiTiLeZarD/decompose

import argparse
import glob
import os
import subprocess
import json
import platform

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--env", help="Specify the environment to use (default: local)",
                    default="local", choices=["local", "uat", "production", "front"])
parser.add_argument("-g", "--group", action="append", help="Specify a group of services", default=[])
parser.add_argument("-c", "--configfile", help="Specify a config file", default='decompose.conf.json')
parser.add_argument("-p", "--path", default=os.getcwd(), help="Path to find the root of modules")
parser.add_argument("-pr", "--path_relative", default=None, help="Use relative path (can use a variable here)")
parser.add_argument("--substitute", action="append", help="Other substitutions", default=[])
parser.add_argument("-mp", "--modules_path", default='modules', help="Path to find modules from root")
parser.add_argument("-o", "--output", default='docker-compose.yml', help="File in which the config will be saved")
parser.add_argument("--dockercompose_version", default='3.8', help="Target a specific dockercompose version")
parser.add_argument("-s", "--service", action="append", help="Specify a service", default=[])

arguments = parser.parse_args()


def getPath(*args):
    return '/'.join([arguments.path] + list(args))


def getConfig():
    if not os.path.isdir(arguments.path):
        raise Exception('{0} is not a valid path'.format(arguments.path))

    configfile = arguments.configfile
    if not os.path.isfile(configfile):
        configfile = getPath(arguments.configfile)
        if not os.path.isfile(configfile):
            raise Exception('{0} could not be found'.format(configfile))

    config = None
    with open(configfile, 'rb') as f:
        config = json.loads(f.read())

    return config


def getAllServices():
    groups = getConfig()['groups']

    for group in arguments.group:
        if group not in groups:
            raise Exception('Group {0} not found'.format(group))

    available_services = set([f.split('/')[-2] for f in glob.glob(getPath(arguments.modules_path, '**/docker-compose.yml'))])
    services = set([s for g in arguments.group for s in groups[g]] + arguments.service)
    services = [s for s in services if s in available_services]
    if len(services) == 0:
        raise Exception("No service selected")

    for service in services:
        if not os.path.isdir(getPath(arguments.modules_path, service)):
            raise Exception("Service {0} could not be found".format(service))

    return services


# gather all common files
common = {}
for common_file in glob.glob(getPath(arguments.modules_path, '*.yml')):
    with open(common_file, 'r') as f:
        common[os.path.basename(common_file)] = f.read()


def use_file(service, env=None, required=True):
    filename = 'docker-compose.{0}yml'.format('' if env is None else '{0}.'.format(env))
    filename = getPath(arguments.modules_path, service, filename)

    if not os.path.isfile(filename):
        if required:
            raise Exception("Service {0} misconfigured (cannot find {1})".format(service, filename))
        return False

    file_content = None
    with open(filename, 'r') as f:
        file_content = f.read()

    file_content = file_content.replace('##VERSION##', 'version: "{0}"'.format(arguments.dockercompose_version))
    for item in common:
        file_content = file_content.replace('# include {0}'.format(item), common[item])
    file_content = file_content.replace('#<<: *', '<<: *')

    filename = getPath('{0}_{1}'.format(service, os.path.basename(filename)))
    with open(filename, 'w') as f:
        f.write(file_content)

    return filename


if __name__ == '__main__':
    if arguments.env not in getConfig()['environments']:
        raise Exception('{0} is not a valid environment'.format(arguments.env))

    # create a folder with all files ready for docker-compose
    compose_files = []
    for service in getAllServices():
        compose_files.append(use_file(service))
        compose_files.append(use_file(service, env=arguments.env))
        compose_files.append(use_file(service, env=platform.machine(), required=False))

    docker_compose_command = ['docker-compose']
    env_file = getPath('.env.{0}'.format(arguments.env))
    if os.path.isfile(env_file):
        docker_compose_command.append('--env-file')
        docker_compose_command.append(env_file)
    for compose_file in compose_files:
        docker_compose_command.append('-f')
        docker_compose_command.append(compose_file)
    docker_compose_command.append('config')

    try:
        config = subprocess.check_output(docker_compose_command).decode('utf-8')

        dockercompose_file = getPath(arguments.output)
        if arguments.path_relative is not None:
            config = config.replace(os.path.abspath(getPath()), arguments.path_relative)

        for substitution in arguments.substitute:
            config = config.replace(*substitution.split(' '))

        with open(dockercompose_file, 'w') as f:
            f.write(config)

    except subprocess.CalledProcessError as e:
        print("---- ERROR -----")
        print(e.stderr)
        print("----------------")
    finally:
        for compose_file in compose_files:
            os.unlink(compose_file)
