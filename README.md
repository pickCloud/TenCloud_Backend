# Dashboard
控制台

# 项目预备

### 安装包
pip install -r requirements.txt

### 创建setting.py
复制setting_sample.py的内容

### 创建DB
##### 数据库ten_dashboard
CREATE DATABASE IF NOT EXISTS ten_dashboard DEFAULT CHARSET utf8;
##### 测试表for_test
CREATE TABLE IF NOT EXISTS for_test (id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, name varchar(20) DEFAULT NULL);
##### 设置用户名和密码
settings['mysql_user'], settings['mysql_password']

### 测试
curl http://localhost:8010/server/status