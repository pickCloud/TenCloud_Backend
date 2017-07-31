#!/bin/sh

base_url="http://console.10.com/supermonitor/"

DownloadFunc() {
    name=${1}
    url=${2}
    stroage=${3}
  curl --retry 3 --retry-delay 2 -s -L -o ${stroage} ${url}
  ret=$?
  if [ ${ret} -ne 0 ];then
    echo "failed to download ${name}"
    exit 1
  else
    echo "success to download ${name}"
fi
}

report_data="report_data.service"
report_data_url=${base_url}+${report_data}
report_data_stroage="/etc/systemd/system/report_data.service"
if [ -f ${report_data_stroage} ];then
    systemctl stop ${report_data}
    systemctl disable ${report_data}
    rm ${report_data_stroage}
fi
DownloadFunc ${report_data} ${report_data_url} ${report_data_stroage}
chmod 644 ${report_data_stroage}

sync_linux_amd64="sync_linux_amd64"
sync_url=${base_url}+${sync_linux_amd64}
sync_storage="/usr/sbin/sync_linux_amd64"
if [ -f ${sync_storage} ];then
    rm ${sync_storage}
fi
DownloadFunc ${sync_linux_amd64} ${sync_url} ${sync_storage}
chmod 755 ${sync_storage}
pid=$(pgrep -f ${sync_linux_amd64})
if pgrep -f ${sync_linux_amd64} > /dev/null; then
    echo "kill old version sync"
    kill ${pid}
fi
echo "create sync"
log="/var/log/report_data"
if [ ! -d ${log} ];then
    mkdir -p ${log}
fi

clean_log_timer="clean-log-daily.timer"
clean_log_timer_url=${base_url}+${clean_log_timer}
clean_log_timer_storage="/etc/systemd/system/clean-log-daily.timer"
if [ -f ${clean_log_timer_storage} ];then
    systemctl stop ${clean_log_timer}
    systemctl disable ${clean_log_timer}
    rm ${clean_log_timer_storage}
fi
DownloadFunc ${clean_log_timer} ${clean_log_timer_url} ${clean_log_timer_storage}
chmod 644 ${clean_log_timer_storage}

clean_log_service="clean-log-daily.service"
clean_log_service_url=${base_url}+${clean_log_service}
clean_log_service_storage="/etc/systemd/system/clean-log-daily.service"
if [ -f ${clean_log_service_storage} ];then
    rm ${clean_log_service_storage}
fi
DownloadFunc ${clean_log_service} ${clean_log_service_url} ${clean_log_service_storage}
chmod 644 ${clean_log_service_storage}

systemctl daemon-reload
systemctl enable ${report_data}
systemctl start ${report_data}
systemctl enable ${clean_log_timer}
systemctl start ${clean_log_timer}