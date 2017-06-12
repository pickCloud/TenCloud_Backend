#!/bin/sh
DownloadFunc() {
    name=${1}
    url=${2}
    stroage=${3}
  curl --retry 3 --retry-delay 2 -s -L -o "${stroage}" "${url}"
  ret=$?
  if [ ${ret} -ne 0 ];then
    echo "failed to download ${name}"
    exit 1
  else
    echo "success to download ${name}"
fi
}
report_data="report_data.service"
report_data_url="http://47.94.18.22/supermonitor/report_data.service"
report_data_stroage="/etc/systemd/system/report_data.service"
if [ -f "${report_data_stroage}" ];then
    systemctl disable "${report_data}"
    rm "${report_data_stroage}"
fi
DownloadFunc ${report_data} ${report_data_url} ${report_data_stroage}
chmod 755 "${report_data_stroage}"
sync_linux_amd64="sync_linux_amd64"
sync_url="http://47.94.18.22/supermonitor/sync_linux_amd64"
sync_storage="/usr/sbin/sync_linux_amd64"
if [ -f "${sync_storage}" ];then
    rm "${sync_storage}"
fi
DownloadFunc ${sync_linux_amd64} ${sync_url} ${sync_storage}
chmod 755 "${sync_storage}"
pid=$(pgrep -f "${sync_linux_amd64}")
if pgrep -f ${sync_linux_amd64} > /dev/null; then
    echo "kill old version sync"
    kill "${pid}"
fi
echo "create sync"
log="/var/log/report_data"
if [ ! -d ${log} ];then
    mkdir -p ${log}
fi
systemctl enable "${report_data}"
systemctl start "${report_data}"
