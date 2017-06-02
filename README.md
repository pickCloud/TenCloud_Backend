# Dashboard
控制台

# 项目预备

## Python环境
python3

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
);
```
* 主机表server
```
CREATE TABLE `server` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主机ID',
  `name` varchar(128) DEFAULT '' COMMENT '主机名称',
  `public_ip` varchar(15) DEFAULT '' COMMENT '主机IP',
  `business_status` tinyint(4) DEFAULT '0' COMMENT '0适用, 1正常, 2锁定, 3过期, 4即将过期',
  `cluster_id` int(11) NOT NULL DEFAULT '1' COMMENT '表cluster的id',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`public_ip`)
);
```

* 主机账户表
```
CREATE TABLE `server_account` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主机账户ID',
  `public_ip` varchar(15) NOT NULL DEFAULT '' COMMENT 'IP',
  `username` varchar(128) NOT NULL COMMENT '主机的用户名',
  `passwd` varchar(256) NOT NULL COMMENT '主机的密码',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `public_ip` (`public_ip`)
);
```

* 实例表
```
CREATE TABLE `instance` (
  `provider` varchar(32) NOT NULL COMMENT '服务商',
  `instance_id` varchar(64) NOT NULL COMMENT '实例ID',
  `instance_name` varchar(128) DEFAULT '' COMMENT '实例名称',
  `region_id` varchar(64) NOT NULL COMMENT '实例所属地区',
  `hostname` varchar(64) DEFAULT '' COMMENT '实例hostname',
  `image_id` varchar(64) DEFAULT '' COMMENT '实例image_id',
  `status` varchar(32) DEFAULT '' COMMENT '实例状态',
  `inner_ip` varchar(15) DEFAULT '' COMMENT '实例内网ip',
  `public_ip` varchar(15) NOT NULL COMMENT '实例外网ip',
  `cpu` tinyint(4) DEFAULT '0' COMMENT 'cpu个数',
  `memory` int(11) DEFAULT '0' COMMENT '实例内存大小',
  `os_name` varchar(64) DEFAULT '' COMMENT '实例操作系统名称',
  `os_type` varchar(64) DEFAULT '' COMMENT '实例操作系统类型',
  `create_time` varchar(17) DEFAULT '' COMMENT '实例创建的时间',
  `expired_time` varchar(17) DEFAULT '' COMMENT '实例过期时间',
  `is_available` tinyint(1) DEFAULT '0' COMMENT '实例是否可用',
  `charge_type` varchar(64) DEFAULT '' COMMENT '实例的付费方式',
  UNIQUE KEY `instance_id` (`instance_id`),
  UNIQUE KEY `public_ip` (`public_ip`)
);
```

## 测试
```
curl http://localhost:8010/api/clusters
```
