#!/bin/sh

sync="http://47.94.18.22/var/www/Dashboard/static/supermonitor/sync"
curl --retry 3 --retry-delay 2 -s -L -O $sync
process=./sync
pid=$(ps -ef|grep $process|grep -v grep|awk '{print $1}')
if echo $pid &> /dev/null; then
    echo "kill old version sync"
    kill $pid
    echo "create new sync"
    setsid $process --token=$1
else
    echo "create new sync"
    setsid $process --token=$1
fi
