# Dashboard
控制台

# 项目预备

## 安装包
* pip install -r requirements.txt

## 创建setting.py
* 复制setting_sample.py的内容并修过

## 创建DB
* 设置用户名和密码
```
settings['mysql_user'], settings['mysql_password']
```
* 数据库ten_dashboard
```
CREATE DATABASE IF NOT EXISTS ten_dashboard DEFAULT CHARSET utf8mb4;
```
* 集群表cluster
```
CREATE TABLE IF NOT EXISTS `cluster` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '集群ID',
  `name` varchar(128) NOT NULL COMMENT '集群名称',
  `description` text COMMENT '集群描述',
  `status` tinyint(4) DEFAULT '0' COMMENT '集群状态，以后添加',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4
```
* 主机表server
```
CREATE TABLE `server` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主机ID',
  `name` varchar(128) DEFAULT '' COMMENT '主机名称',
  `address` varchar(128) DEFAULT '' COMMENT '主机地址',
  `ip` varchar(15) DEFAULT '' COMMENT '主机IP',
  `owner` varchar(50) DEFAULT '' COMMENT '某个员工、部门、项目',
  `machine_status` tinyint(4) DEFAULT '1' COMMENT '0运行中, 1已停止, 2启动中, 3停止中, 4满负载',
  `business_status` tinyint(4) DEFAULT '0' COMMENT '0适用, 1正常, 2锁定, 3过期, 4即将过期',
  `cluster_id` int(11) NOT NULL COMMENT '表cluster的id',
  `os` varchar(50) DEFAULT '' COMMENT '操作系统',
  `cpu` varchar(50) DEFAULT '' COMMENT 'CPU',
  `memory` varchar(50) DEFAULT '' COMMENT '内存',
  `disk` varchar(50) DEFAULT '' COMMENT '硬盘',
  `network` varchar(50) DEFAULT '' COMMENT '网络',
  `feature` varchar(50) DEFAULT '' COMMENT '机器特征',
  `provider` varchar(50) DEFAULT '' COMMENT '服务商',
  `period` varchar(20) DEFAULT '' COMMENT '周期',
  `pay_type` tinyint(4) DEFAULT '0' COMMENT '缴费方式, 0按年, 1按月',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
)
```

## 测试
```
curl http://localhost:8010/api/clusters
```
