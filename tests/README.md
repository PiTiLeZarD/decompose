# to test

-   ./decompose.py -p tests -g local -e local
-   ./decompose.py -p tests -g uat -e uat
-   ./decompose.py -p tests -g production -e production
-   ./decompose.py -p tests -s adminer -s db -e local
-   ./decompose.py -p tests -s web -e local -pr '\${TEST}'

Note: in these tests, groups match environments, it doesn't have to. In our environment we use services as group names. Also as convenience you can have a first name "-g jono" would be the config I use all the time.
