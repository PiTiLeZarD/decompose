# decompose

Modularise docker-compose.

A bit of background: In my team we have people working on different section of a multi service application. We don't all
need to run everyone else's services. Also we have multiple swarm environments. The UAT environment runs all services but
we have 2 productions swarms running different types of services.

The issue was, having one docker-compose file was not maintainable.

The solution is: modules (for us anyway)

I've been using this script for a while and I'm confident it helps us in managing all our environments very efficiently
so I thought I'd make it available open source.

# concepts

-   A service is a folder with a docker-compose.yml and docker-compose.{environment}.yml files to go along with it.
-   A group is a collection of services working together.
-   An environment is a target configuration for all services
-   decompose will generate a docker-compose.yml file specific to a list of services for a given environment
-   if a .env.{environment} file is available at the root, it will be used by decompose.py
