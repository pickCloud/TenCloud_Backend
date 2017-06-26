package main

import (
	"bytes"
	"encoding/json"
	"io/ioutil"
	"math"
	"net/http"
	"regexp"
	"time"

	"flag"

	"github.com/qiniu/log"
	gcpu "github.com/shirou/gopsutil/cpu"
	gdisk "github.com/shirou/gopsutil/disk"
	gmem "github.com/shirou/gopsutil/mem"
)

const (
	dateformat    = "2006-01-02 15:04:05"
	getipURL      = "http://ip-api.com/json"
	debugURL      = "http://192.168.199.139:8010/remote/server/report"
	productionURL = "http://47.94.18.22/remote/server/report"
)

var (
	debug    = flag.Bool("debug", true, "debug is distinguish  environment, --debug=true")
	interval = flag.Int64("interval", 30, "interval is app report data interval, --interval=30")
	cputick  = flag.Int64("cputick", 1, "cputick is cpu interval, --cputick=1")
	dir      = flag.String("dir", "/var/log/report_data/", "dir is the directory to save dir, --dir=/var/log/report_data")
)

type app struct {
	server   string
	publicIP string
	interval time.Duration
	cpuTick  time.Duration
	logger   *log.File
}

func newapp(publicIP, server string, interval, tick int64, log *log.File) *app {
	return &app{
		publicIP: publicIP,
		server:   server,
		interval: time.Duration(interval) * time.Second,
		cpuTick:  time.Duration(tick) * time.Second,
		logger:   log,
	}
}
func (a *app) setServer(server string) {
	a.server = server
	return
}
func (a *app) getPublicIP() {
	resp, err := http.Get(getipURL)
	if err != nil {
		a.logger.Error("[getPublicIP] responsed with errpr:%s", err)
		return
	}
	if resp.StatusCode != http.StatusOK {
		a.logger.Errorf("[getPublicIP] http response status code is not equal to 200,  http status code:%d", resp.StatusCode)
		return
	}
	defer resp.Body.Close()
	b, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		a.logger.Errorf("[getPublicIP] responsed with errpr:%s", err)
		return
	}
	re := regexp.MustCompile(`\d+\.\d+\.\d+\.\d+`)
	a.publicIP = re.FindString(string(b))
	return
}

func round(f float64, n int) float64 {
	pow10 := math.Pow10(n)
	resp := float64(int(f*pow10)) / pow10
	return resp
}

type cpu struct {
	Percent float64 `json:"percent"`
}

func (a *app) getCPU() (resp cpu) {
	cpus, err := gcpu.Percent(a.cpuTick, false)
	if err != nil {
		a.logger.Errorf("[getcpu] cpu.Percent() return with error", err)
		return
	}
	resp.Percent = round(cpus[0], 2)
	return
}

type memory struct {
	Total     uint64  `json:"total"`
	Percent   float64 `json:"percent"`
	Available uint64  `json:"available"`
	Free      uint64  `json:"free"`
}

func (a *app) getMemory() (resp memory) {
	mem, err := gmem.VirtualMemory()
	if err != nil {
		a.logger.Errorf("[getmem] mem.VirtualMemory() return with error", err)
		return
	}
	resp.Total = mem.Total
	resp.Percent = round(mem.UsedPercent, 2)
	resp.Available = mem.Available
	resp.Free = mem.Free
	return resp
}

type diskUsage struct {
	Total   uint64  `json:"total"`
	Percent float64 `json:"percent"`
	Free    uint64  `json:"free"`
}

func (a *app) getDisk() (resp diskUsage) {
	disk, err := gdisk.Usage("/")
	if err != nil {
		a.logger.Errorf("[getDisk] disk.Usage() return with error", err)
		return
	}
	resp.Total = disk.Total
	resp.Percent = round(disk.UsedPercent, 2)
	resp.Free = disk.Free
	return resp
}

type stat struct {
	IP        string    `json:"public_ip"`
	CPU       cpu       `json:"cpu"`
	MEM       memory    `json:"memory"`
	Disk      diskUsage `json:"disk"`
	TimeStamp int64     `json:"time"`
}

func (a *app) sendStat() {
	a.logger.Infof("start this push at %s", time.Now().String())
	stat := stat{
		IP:        a.publicIP,
		CPU:       a.getCPU(),
		MEM:       a.getMemory(),
		Disk:      a.getDisk(),
		TimeStamp: time.Now().Unix(),
	}
	a.logger.Infof("push data %+v", stat)
	b, err := json.Marshal(&stat)
	if err != nil {
		a.logger.Errorf("[sendStat] json.Marshal return with error %s, stat: %+v", err, stat)
		return
	}
	reader := bytes.NewReader(b)
	resp, err := http.Post(a.server, "application/json", reader)
	if err != nil {
		a.logger.Error("[sendStat] http.Post() return with error:", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		a.logger.Errorf("[sendStat] responsed http code:%d", resp.StatusCode)
	}
	a.logger.Infof("end this push at %s", time.Now().String())
	return
}
func main() {
	flag.Parse()
	server, ip, logLevel := debugURL, "127.0.0.1", "DEBUG"
	logger := log.NewFile(*dir+"report_data", log.Level(logLevel))
	logger.SetRotate(log.RotateDate)
	app := newapp(ip, server, *interval, *cputick, logger)
	if !*debug {
		server = productionURL
		app.getPublicIP()
		app.setServer(server)
	}
	app.logger.Info("start push data to server")
	//app.sendStat()
	//tick := time.NewTicker(app.interval)
	//defer tick.Stop()
	//for _ = range tick.C {
	//app.sendStat()
	//}
	for {
		app.sendStat()
		time.Sleep(app.interval)
	}
}
