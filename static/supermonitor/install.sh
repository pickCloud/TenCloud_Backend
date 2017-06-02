#!/bin/sh
sync_linux_amd64="sync_linux_amd64"
if ls $(pwd) | grep ${sync_linux_amd64};then
    rm ${sync_linux_amd64}
fi
url="http://47.94.18.22/supermonitor/sync_linux_amd64"
curl --retry 3 --retry-delay 2 -s -L -O $url
ret=$?
if [ ${ret} -ne 0 ];then
    echo "failed to download sync_linux_amd64"
    exit 1
else
    echo "success to download sync_linux_amd64"
fi
pid=$(ps -ef|grep ${sync_linux_amd64}|grep -v grep|awk '{print $2}')
if ps -ef|grep ${sync_linux_amd64}|grep -v grep > /dev/null; then
    echo "kill old version sync"
    kill ${pid}
    echo "restart sync with new version"
    chmod +x ${sync_linux_amd64}
    ./sync_linux_amd64 --debug=false &
else
    echo "create sync"
    chmod +x ${sync_linux_amd64}
    ./sync_linux_amd64 --debug=false --internel=60 &
fi
