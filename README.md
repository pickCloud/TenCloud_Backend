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
* 数据库
```
CREATE DATABASE IF NOT EXISTS ten_dashboard DEFAULT CHARSET utf8mb4;
```
* 集群表
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
* 主机表
```
CREATE TABLE `server` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `name` varchar(128) DEFAULT '',
  `public_ip` varchar(15) DEFAULT '' COMMENT 'IP',
  `business_status` tinyint(4) DEFAULT '0' COMMENT '0, 1, 2, 33, 44',
  `cluster_id` int(11) NOT NULL DEFAULT '1' COMMENT 'clusterid',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `instance_id` varchar(64) NOT NULL DEFAULT '' COMMENT 'instance表的instance_id',
  `cid` int(11) NOT NULL DEFAULT '1' COMMENT 'company表id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `instance_id` (`instance_id`),
  UNIQUE KEY `ip` (`public_ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 镜像仓库
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

ALTER TABLE instance ADD COLUMN region_name varchar(20) NOT NULL DEFAULT '' COMMENT '实例所属地区名称'

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

* 项目表
```
CREATE TABLE `project` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `name` varchar(128) NOT NULL COMMENT '项目名称',
  `description` text COMMENT '项目描述',
  `repos_name` varchar(128) NOT NULL DEFAULT '' COMMENT '项目仓库名称',
  `status` tinyint(4) DEFAULT '0' COMMENT '项目状态: 0 初创建, 1 构建中, 2 构建成功, 3 部署中， 4 部署成功, -2 构建失败, -4 部署失败''',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `repos_url` varchar(512) NOT NULL DEFAULT '' COMMENT '项目仓库地址',
  `mode` tinyint(4) DEFAULT '0' COMMENT '项目类型: 0 普通项目, 1 基础服务, 2 应用组件',
  `http_url` varchar(512) NOT NULL DEFAULT '' COMMENT 'githubhttp',
  `image_name` varchar(128) NOT NULL DEFAULT '',
  `deploy_ips` varchar(128) NOT NULL DEFAULT '',
  `container_name` varchar(128) NOT NULL DEFAULT '',
  `image_source` tinyint(4) NOT NULL,
  `cid` int(11) NOT NULL DEFAULT '1' COMMENT 'company表id',
  PRIMARY KEY (`id`),
  UNIQUE KEY `repos_url` (`repos_url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


```

* 项目版本表
```
CREATE TABLE `project_versions` (
     `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '项目版本id',
     `name` varchar(128) NOT NULL COMMENT '项目名字',
     `version` varchar(128) NOT NULL DEFAULT '' COMMENT '项目版本',
     `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
     `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
     PRIMARY KEY (`id`)
 )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE UNIQUE INDEX name_version on project_versions (name, version);
ALTER TABLE project_versions ADD COLUMN log longtext COMMENT '构建日志';
```

* 用户表
```
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `mobile` varchar(11) NOT NULL COMMENT '用户手机',
  `email` varchar(128) NOT NULL DEFAULT '' COMMENT '用户邮箱',
  `name` varchar(64) NOT NULL DEFAULT '' COMMENT '用户名字',
  `password` varchar(256) NOT NULL DEFAULT '' COMMENT '用户密码',
  `image_url` varchar(128) NOT NULL DEFAULT '' COMMENT '用户头像url',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mobile` (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE user ADD COLUMN gender tinyint(4) COMMENT '性别 1: 男性 2: 女性 3: 未知'
ALTER TABLE user ADD COLUMN birthday int(10) COMMENT '生日'
ALTER TABLE user ADD COLUMN password_strength varchar(64) not null DEFAULT '' COMMENT '密码强度'
```

* 文件表
```
CREATE TABLE `filehub` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `filename` varchar(128) NOT NULL DEFAULT '' COMMENT '文件名',
  `size` int(11) unsigned DEFAULT '0' COMMENT '文件大小',
  `qiniu_id` varchar(128) NOT NULL DEFAULT '' COMMENT '文件在七牛的id',
  `owner` int(11) unsigned NOT NULL COMMENT '上传文件者，对应user表id',
  `mime` varchar(64) NOT NULL DEFAULT '' COMMENT '文件类型',
  `hash` varchar(128) NOT NULL DEFAULT '' COMMENT '文件hash',    
  `type` tinyint(2) unsigned NOT NULL DEFAULT '0' COMMENT '0表示文件, 1表示文件夹',
  `pid` int(11) unsigned NOT NULL DEFAULT '0' COMMENT '树形结构的父节点',
  `cid` int(11) DEFAULT '1' COMMENT 'company表id',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE filehub ADD COLUMN upload_status tinyint(2) unsigned NOT NULL DEFAULT '0' COMMENT '文件上传状态, 0未上传，1上传成功'
ALTER TABLE filehub DROP COLUMN upload_status

ALTER TABLE `filehub` drop column cid
ALTER TABLE `filehub` add column lord int(11) not null
ALTER TABLE `filehub` ADD COLUMN `form` tinyint(4) not null default 1 COMMENT '所有者类型 1个人/2公司'
```

* 机器记录时平均维护表
```
CREATE TABLE `server_log_hour` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `public_ip` varchar(15) not null,
    `start_time` int(10) not null,
    `end_time` int(10) not null,
    `cpu_log` json not null,
    `disk_log` json not null,
    `memory_log` json not null,
    `net_log`  json not null 
)
create index ip_time on server_log_hour (public_ip, start_time, end_time);
```

* 容器记录时平均维护表
```
CREATE TABLE `container_log_hour` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `public_ip` varchar(15) not null,
    `container_name` varchar(128) not null,
    `start_time` int(10) not null,
    `end_time` int(10) not null,
    `content` json not null
);
create index hour_ip_time on container_log_hour (public_ip, container_name, start_time, end_time);
```

* 容器记录天平均维护表
```
CREATE TABLE `container_log_day` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `public_ip` varchar(15) not null,
    `container_name` varchar(128) not null,
    `start_time` int(10) not null,
    `end_time` int(10) not null,
    `content` json not null
);
create index day_ip_time on container_log_day (public_ip, container_name, start_time, end_time);
```

* 机器记录天平均维护表
```
CREATE TABLE `server_log_day` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `public_ip` varchar(15) not null,
    `start_time` int(10) not null,
    `end_time` int(10) not null,
    `cpu_log` json not null,
    `disk_log` json not null,
    `memory_log` json not null,
    `net_log`  json not null
)
create index ip_time on server_log_day (public_ip, start_time, end_time);
```

* 机器操作记录
```
CREATE TABLE `operation_log` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `user_id`  int(11) unsigned NOT NULL,
    `object_id` varchar(15) NOT NULL COMMENT '操作对象',
    `object_type` tinyint(4) NOT NULL COMMENT '操作对象类型',
    `operation` tinyint(4) unsigned NOT NULL DEFAULT 3 COMMENT '操作行为状态码，具体操作根据操作对象更改',
    `operation_status` tinyint(4) unsigned NOT NULL DEFAULT 0 COMMENT '0:失败,1:成功',
    `created_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
create index object_id on operation_log (object_id);
```

* 公司表
```
CREATE TABLE `company` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `name` varchar(128) NOT NULL COMMENT '名称',
  `contact` varchar(128) NOT NULL COMMENT '联系人',
  `mobile` varchar(11) NOT NULL COMMENT '联系方式',
  `description` text,
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 公司员工表
```
CREATE TABLE `company_employee` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `cid` int(11) NOT NULL COMMENT 'company表ID',
  `uid` int(11) NOT NULL COMMENT 'user表ID',
  `is_admin` tinyint(1) NOT NULL DEFAULT '0' COMMENT '管理员',
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '-1拒绝, 0审核中, 1通过, 2创始人',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 公司员工加入条件表
```
CREATE TABLE `company_entry_setting` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `cid` int(11) NOT NULL COMMENT 'company表ID',
  `setting` varchar(64) NOT NULL COMMENT '条件配置包含user表的字段名',
  `code` varchar(7) NOT NULL COMMENT 'company_id与setting的hash值',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `company_id` (`cid`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 消息表
```
CREATE TABLE `message` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `owner` int(11) NOT NULL COMMENT 'user表ID',
  `content` varchar(256) DEFAULT NULL,
  `mode` tinyint(4) NOT NULL DEFAULT '1' COMMENT '1加入企业，2企业改变信息',
  `sub_mode` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0马上审核, 1重新提交, 2进入企业, 3马上查看',
  `tip` varchar(64) NOT NULL DEFAULT '' COMMENT 'cid:code',
  `status` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0未读，1已读',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `owner_status` (`owner`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 权限模版表
```
CREATE TABLE `permission_template` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `name` varchar(64) NOT NULL COMMENT '权限模版名称',
  `cid` int(11) NOT NULL COMMENT '表company对应的ID',
  `permissions` varchar(512) NOT NULL DEFAULT '' COMMENT '表permission对应的id集合, 比如1,2,3',
  `access_servers` varchar(1024) NOT NULL DEFAULT '' COMMENT '表server对应的id集合, 比如1,2,3',
  `access_projects` varchar(1024) NOT NULL DEFAULT '' COMMENT '表project对应的id集合, 比如1,2,3',
  `access_filehub` varchar(1024) NOT NULL DEFAULT '' COMMENT '表filehub对应的id集合, 比如1,2,3',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  ｀type` tinyint(4) not null default 1 COMMENT '权限模版类型，0:预设,1:新增',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 权限表
```
CREATE TABLE `permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `name` varchar(64) NOT NULL COMMENT '权限名称',
  `group` tinyint(4) NOT NULL COMMENT '权限组, 0云服务器, 1项目, 2文件服务, 3企业资料, 4员工管理, 5权限模版管理, 6平台管理',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 用户权限表
```
CREATE TABLE `user_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `uid` int(11) NOT NULL COMMENT '表user的ID',
  `pid` int(11) NOT NULL COMMENT '表permission的ID',
  `cid` int(11) NOT NULL COMMENT '表company的ID',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 用户可访问云服务器表
```
CREATE TABLE `user_access_server` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `uid` int(11) NOT NULL COMMENT '表user的ID',
  `sid` int(11) NOT NULL COMMENT '表server的ID',
  `cid` int(11) NOT NULL COMMENT '表company的ID',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 用户可访问项目表
```
CREATE TABLE `user_access_project` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `uid` int(11) NOT NULL COMMENT '表user的ID',
  `pid` int(11) NOT NULL COMMENT '表project的ID',
  `cid` int(11) NOT NULL COMMENT '表company的ID',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

* 用户可访问文件表
```
CREATE TABLE `user_access_filehub` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `uid` int(11) NOT NULL COMMENT '表user的ID',
  `fid` int(11) NOT NULL COMMENT '表filehub的ID',
  `cid` int(11) NOT NULL COMMENT '表company的ID',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
