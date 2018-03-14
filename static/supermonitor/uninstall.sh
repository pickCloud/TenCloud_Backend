#!/bin/sh
agent_service="tencloud-agent.service"
agent_service_stroage="/etc/systemd/system/tencloud-agent.service"
if [ -f ${agent_service_stroage} ];then
    echo "delete old version tencloud-agent service"
    sudo systemctl stop ${agent_service}
    sudo systemctl disable ${agent_service}
    sudo rm ${agent_service_stroage}
fi

agent_storage="/usr/sbin/agent"
if [ -f ${agent_storage} ];then
    echo "delete old version tencloud-agent"
    sudo rm ${agent_storage}
fi

log="/var/log/tencloud-agent"
if [ -d ${log} ];then
    echo "delete old version tencloud-agent log"
    sudo rm -rf ${log}
fi