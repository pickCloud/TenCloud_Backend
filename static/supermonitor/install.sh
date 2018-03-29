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
ExecStart=/usr/sbin/tencloud-agent --debug=${debug} --interval=30 --addr=${addr}

[Install]
WantedBy=multi-user.target
EOF
}

RemoveOldVersion() {
    addr=$1
    curl -sSL $addr | sh
}
uninstall_url=${base_url}/supermonitor/uninstall.sh
RemoveOldVersion ${uninstall_url}

agent_service="tencloud-agent.service"
agent_service_storage="/etc/systemd/system/tencloud-agent.service"
GenerateServiceFunc ${upload_url} ${debug} ${agent_service}
sudo mv ${agent_service} ${agent_service_storage}
sudo chmod 644 ${agent_service_storage}

agent="tencloud-agent"
agent_url=${base_url}/supermonitor/${agent}
agent_storage="/usr/sbin/tencloud-agent"
DownloadFunc ${agent} ${agent_url} ${agent_storage}
sudo chmod 755 ${agent_storage}

echo "create tencloud agent log"
log="/var/log/tencloud-agent"
if [ ! -d ${log} ];then
    sudo mkdir -p ${log}
fi

sudo systemctl daemon-reload
sudo systemctl enable ${agent_service}
sudo systemctl start ${agent_service}
