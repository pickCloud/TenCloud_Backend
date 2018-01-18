#!/bin/sh

base_url=$1
debug=$2
upload_url=${base_url}/remote/server/report

echoerr() {
    echo "$@" 1>&2;
}

`sudo hostname -b localhost`

DownloadFunc() {
    name=${1}
    url=${2}
    storage=${3}
  sudo curl --retry 3 --retry-delay 2 -s -L -o ${storage} ${url}
  ret=$?
  if [ ${ret} -ne 0 ];then
    echoerr "failed to download ${name}"
    exit 1
  else
    echo "success to download ${name}, 请稍等..."
fi
}

GenerateServiceFunc() {
    addr=${1}
    debug=${2}
    name=${3}
    cat>${name}<<EOF
[Unit]
Description=auto run TenCloud agent
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=root
Group=root
Restart=always
RestartSec=1
ExecStart=/usr/sbin/sync_linux_amd64 --debug=${debug} --interval=60 --addr=${addr}

[Install]
WantedBy=multi-user.target
EOF
}
report_data="report_data.service"
report_data_storage="/etc/systemd/system/report_data.service"
if [ -f ${report_data_storage} ];then
    sudo systemctl stop ${report_data}
    sudo systemctl disable ${report_data}
    sudo rm ${report_data_storage}
fi
GenerateServiceFunc ${upload_url} ${debug} ${report_data}
sudo mv ${report_data} ${report_data_storage}
sudo chmod 644 ${report_data_storage}

sync_linux_amd64="sync_linux_amd64"
sync_url=${base_url}/supermonitor/${sync_linux_amd64}
sync_storage="/usr/sbin/sync_linux_amd64"
if [ -f ${sync_storage} ];then
    sudo rm ${sync_storage}
fi
DownloadFunc ${sync_linux_amd64} ${sync_url} ${sync_storage}
sudo chmod 755 ${sync_storage}
pid=$(pgrep -f ${sync_linux_amd64})
if pgrep -f ${sync_linux_amd64} > /dev/null; then
    echo "kill old version sync"
    sudo kill ${pid}
fi
echo "create sync"
log="/var/log/report_data"
if [ ! -d ${log} ];then
    sudo mkdir -p ${log}
fi

sudo systemctl daemon-reload
sudo systemctl enable ${report_data}
sudo systemctl start ${report_data}
