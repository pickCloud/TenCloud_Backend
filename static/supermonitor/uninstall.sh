#!/bin/sh
report_data="report_data.service"
report_data_stroage="/etc/systemd/system/report_data.service"
if [ -f ${report_data_stroage} ];then
    sudo systemctl stop ${report_data}
    sudo systemctl disable ${report_data}
    sudo rm ${report_data_stroage}
fi

sync_linux_amd64="sync_linux_amd64"
pid=$(pgrep -f ${sync_linux_amd64})
if pgrep -f ${sync_linux_amd64} > /dev/null; then
    echo "kill old version sync"
    sudo kill ${pid}
fi
sync_storage="/usr/sbin/sync_linux_amd64"
if [ -f ${sync_storage} ];then
    sudo rm ${sync_storage}
fi

log="/var/log/report_data"
if [ -d ${log} ];then
    sudo rm -rf ${log}
fi