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
  `cluster_id` int(11) NOT NULL DEFAULT '0' COMMENT '表cluster的id',
  `os` varchar(50) DEFAULT '' COMMENT '操作系统',
  `cpu` text COMMENT 'cpu json数据',
  `memory` text COMMENT 'memory json数据',
  `disk` text COMMENT 'disk json数据',
  `network` text COMMENT 'network json数据',
  `feature` varchar(50) DEFAULT '' COMMENT '机器特征',
  `provider` varchar(50) DEFAULT '' COMMENT '服务商',
  `period` varchar(20) DEFAULT '' COMMENT '周期',
  `pay_type` tinyint(4) DEFAULT '0' COMMENT '缴费方式, 0按年, 1按月',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ip` (`ip`)
)
```

* 镜像仓库 imagehub
```
CREATE TABLE IF NOT EXISTS `imagehub` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '镜像ID',
  `name` varchar(128) NOT NULL COMMENT '镜像名称',
  `url` varchar(128) COMMENT '镜像url',
  `versions` varchar(128) COMMENT '镜像版本号',
  `description` text COMMENT '描述',
  `source` varchar(50) COMMENT '镜像来源',
  `type` varchar(50) COMMENT '镜像类型',
  `comments` varchar(200) COMMENT '配置说明',
  `status` tinyint(4) DEFAULT '0' COMMENT '镜像状态',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4
```
*镜像类型映射表
```
CREATE TABLE IF NOT EXISTS `image_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `type_id` tinyint(4) NOT NULL UNIQUE COMMENT '镜像类型ID',
  `name` varchar(50) NOT NULL COMMENT '镜像类型名',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4;

INSERT INTO image_types (type_id, name) VALUES (1, '操作系统'),(2, '数据库'),(3, '服务器');
```
*镜像来源映射表
```
CREATE TABLE IF NOT EXISTS `image_sources` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `source_id` tinyint(4) NOT NULL UNIQUE COMMENT '镜像来源ID',
  `name` varchar(50) NOT NULL COMMENT '镜像来源名',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4;

INSERT INTO image_sources (source_id, name) VALUES (1, 'Dockerhub'),(2, 'TenCom'),(3, '自定义');

```
*镜像仓库测试数据
```
INSERT INTO imagehub (name, url, versions, description, source, type, comments) VALUES ('Ubuntu','www.jmkbio.com','16.04',
'Ubuntu是一个自由、开源、基于Debian的Linux发行版，发行周期为6个月，由 Canonical 公司和自由软件社区开发。 本镜像从Docker Hub 同步并由 DaoCloud 提供中文文档支持，用来帮助国内开发者更方便的使用 Docker 镜像。','2',
'1','docker pull www.jmkbio.com/tencom/ubuntu:tag'); 

INSERT INTO imagehub (name, url, versions, description, source, type, comments) VALUES ('Mysql','www.jmkbio.com','5.17.8',
'MySQL 由于其性能高、成本低、可靠性好，已经成为全球最流行的开源数据库软件，被广泛地被应用在 Internet 上的中小型网站中。本镜像从 Docker Hub 同步并由 DaoCloud 提供中文文档支持，用来帮助国内开发者更方便的使用 Docker 镜像。','2',
'2','docker pull www.jmkbio.com/tencom/mysql:tag');
 
 INSERT INTO imagehub (name, url, versions, description, source, type, comments) VALUES ('Mysql','www.jmkbio.com','5.17.8',
'MySQL 由于其性能高、成本低、可靠性好，已经成为全球最流行的开源数据库软件，被广泛地被应用在 Internet 上的中小型网站中。','3',
'2','docker pull www.jmkbio.com/tencom/mysql:tag'); 

```

*主机账户表
```
CREATE TABLE `server_account` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主机账户ID',
  `ip` varchar(15) NOT NULL COMMENT 'IP',
  `username` varchar(128) NOT NULL COMMENT '主机的用户名',
  `passwd` varchar(256) NOT NULL COMMENT '主机的密码',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
)
```

## 测试
```
curl http://localhost:8010/api/clusters
```
