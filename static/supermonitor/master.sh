token=$1
pip install psutil
pip install requests
curl -sSL http://47.94.18.22/supermonitor/report.py > /var/report.py
python /var/report.py ${token} &