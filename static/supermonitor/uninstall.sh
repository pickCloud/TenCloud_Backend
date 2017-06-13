#!/bin/sh
report_data="report_data.service"
report_data_stroage="/etc/systemd/system/report_data.service"
if [ -f ${report_data_stroage} ];then
    systemctl stop ${report_data}
    systemctl disable ${report_data}
    rm ${report_data_stroage}
fi
sync_linux_amd64="sync_linux_amd64"
pid=$(pgrep -f ${sync_linux_amd64})
if pgrep -f ${sync_linux_amd64} > /dev/null; then
    echo "kill old version sync"
    kill ${pid}
fi
sync_storage="/usr/sbin/sync_linux_amd64"
if [ -f ${sync_storage} ];then
    rm ${sync_storage}
fi
clean_log_timer="clean-log-daily.timer"
clean_log_timer_storage="/etc/systemd/system/clean-log-daily.timer"
if [ -f ${clean_log_timer_storage} ];then
    systemctl stop ${clean_log_timer}
    systemctl disable ${clean_log_timer}
    rm ${clean_log_timer_storage}
fi
clean_log_service_storage="/etc/systemd/system/clean-log-daily.service"
if [ -f ${clean_log_service_storage} ];then
    rm ${clean_log_service_storage}
fi
log="/var/log/report_data"
if [ -d ${log} ];then
    rm -rf ${log}
fi