#!/bin/bash

HOSTNAME="127.0.0.1"
PORT="3306"
USERNAME="root"
PASSWORD="hga1016xm."

DBNAME="ten_dashboard"
TABLES=("disk" "cpu")

date
DEL_TIME=$(date --date="7 days ago" '+%s')

for table in "${TABLES[@]}"
do
  del_sql="delete from ${table} where created_time<=${DEL_TIME}"
  echo "${del_sql}"
  mysql -h${HOSTNAME}   -P${PORT}   -u${USERNAME} -p${PASSWORD} ${DBNAME} -e "${del_sql}"
done

