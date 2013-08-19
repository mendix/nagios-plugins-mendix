#!/bin/bash
IFS=$'\n'

pg_clusters=`/usr/bin/pg_lsclusters | sed 1d`
critical=0
output_critical=""
output_ok=""

for i in $pg_clusters; do 
    pg_version=`echo $i | awk '{print $1}'`
    pg_cluster=`echo $i | awk '{print $2}'`
    pg_port=`echo $i | awk '{print $3}'`
    pg_status=`echo $i | awk '{print $4}'`

    if [ $pg_status = "down" ]; then
        critical=1
        if [ -z $output_critical ]; then
            output_critical="Postgresql $pg_version/$pg_cluster status is down"
        else
            output_critical="$output, Postgresql $pg_version/$pg_cluster status is down"
        fi
    else
        test_pg_connection=`/usr/bin/psql --cluster $pg_version/$pg_cluster --list`
        psql_exit_status=$?

        if [ $psql_exit_status -ne 0 ]; then
            if [ -z $output_critical ]; then
                output_critical="pg_lsclusters says that $pg_version/$pg_cluster is up but cannot connect to port $pg_port"
            else
                output_critical="$output, pg_lsclusters says that $pg_version/$pg_cluster is up but cannot connect to port $pg_port"
            fi
            critical=1
        else
            if [ -z $output_ok ]; then
                output_ok="Postgresql: $pg_version/$pg_cluster is ok"
            else
                output_ok="$output_ok, Postgresql: $pg_version/$pg_cluster is ok"
            fi
        fi
    fi
done

if [ $critical -eq 1 ]; then
    echo "$output_critical"
    exit 1;
else
    echo "$output_ok"
    exit 0;
fi
