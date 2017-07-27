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
* 镜像类型映射表
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
* 镜像来源映射表
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
* 镜像仓库测试数据
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

* cpu表
```
create table ten_dashboard.cpu (
	id int auto_increment primary key,
	public_ip varchar(15) not null,
	created_time int(10) not null,
	content json null
) comment 'cpu使用情况';
create index ip_time on cpu (public_ip, created_time);
```

* memory表
```
create table ten_dashboard.memory (
	id int auto_increment primary key,
	public_ip varchar(15) not null,
	created_time int(10) not null,
	content json null 
) comment 'memory使用情况';
create index ip_time on memory (public_ip, created_time);
```

* disk表
```
create table ten_dashboard.disk (
	id int auto_increment primary key,
	public_ip varchar(15) not null,
	created_time int(10) not null,
	content json null
) comment 'disk使用情况';
create index ip_time on disk (public_ip, created_time);
```

* net表
```
create table ten_dashboard.net (
	id int auto_increment primary key,
	public_ip varchar(15) not null,
	created_time int(10) not null,
	content json null
) comment 'net使用情况';
create index ip_time on net (public_ip, created_time);
```

* docker_stat表
```
create table ten_dashboard.docker_stat (
	id int auto_increment primary key,
	public_ip varchar(15) not null,
	container_name varchar(255) not null,
	created_time int(10) not null,
	content json null
) comment 'docker应用使用情况';
create index ip_container_time on docker_stat (public_ip, container_name, created_time);
```

* 项目表 project
```
CREATE TABLE `project` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `name` varchar(128) NOT NULL COMMENT '项目名称',
  `description` text COMMENT '项目描述',
  `repos_name` varchar(128) NOT NULL DEFAULT '' COMMENT '项目仓库名称',
  `status` tinyint(4) DEFAULT '0' COMMENT '项目最新状态: 0 无, 1 构建成功, 2 部署成功, -1 构建失败, -2 部署失败',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `repos_url` varchar(512) NOT NULL DEFAULT '' COMMENT '项目仓库地址',
  `mode` tinyint(4) DEFAULT '0' COMMENT '项目类型: 0 普通项目, 1 基础服务, 2 应用组件',
  PRIMARY KEY (`id`),
  UNIQUE KEY `repos_url` (`repos_url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE project ADD COLUMN http_url varchar(512) NOT NULL DEFAULT '' COMMENT '项目在github的http地址'
ALTER TABLE project ADD COLUMN image_name varchar(128) NOT NULL DEFAULT '' COMMENT '镜像名字'
```

* 项目版本表 project_versions
```
CREATE TABLE `project_versions` (
     `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '项目版本id',
     `name` varchar(128) NOT NULL COMMENT '镜像名字',
     `version` varchar(128) NOT NULL DEFAULT '' COMMENT '项目版本',
     `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
     `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     PRIMARY KEY (`id`)
 )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE UNIQUE INDEX name_version on project_versions (name, version);

```

## 测试
```
curl http://localhost:8010/api/clusters
```

## apidoc
```
0. 安装: npm install -g cnpm --registry=https://registry.npm.taobao.org
        cnpm install apidoc -g
1. 生成: apidoc -f ".*\\.py$" -i . -o ./static/apidoc
2. 查看: cd static/apidoc && python -m http.server
```