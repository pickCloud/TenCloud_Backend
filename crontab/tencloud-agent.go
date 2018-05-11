package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
	"time"

	rotatelogs "github.com/lestrrat-go/file-rotatelogs"
	"github.com/shirou/gopsutil/disk"
	"github.com/shirou/gopsutil/load"
	"github.com/shirou/gopsutil/mem"
	"github.com/shirou/gopsutil/net"
)

const (
	PRECISION = 2     // 浮点数精确度
	PERNIC    = false // 是否获取所有网卡
	PERCPU    = false // 是否获取所有cpu

	// 获取公共ip
	PublicIP  = "http://ip-api.com/json"
	DefaultIP = "127.0.0.1"

	// log
	LogAge    = 30 * 24 * time.Hour
	LogRotate = 24 * time.Hour

	KiB = 1024
	kB  = 1000
	MiB = 1024 * 1024
	MB  = 1000 * 1000
	GiB = 1024 * 1024 * 1024
	GB  = 1000 * 1000 * 1000

	docker  = "/usr/bin/docker"
	stats   = "stats"
	stream  = "--no-stream"
	format  = "--format"
	pattern = "{{.Name}},{{.Container}},{{.PIDs}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.BlockIO}},{{.NetIO}}"

	cat    = "/bin/cat"
	uptime = "/proc/uptime"
)

var (
	addr     = flag.String("addr", "127.0.0.1", "data report address, --addr=http://127.0.0.1")
	interval = flag.Int64("interval", 30, "interval is app report data interval, --interval=30")
	cputick  = flag.Int64("cputick", 1, "cputick is cpu interval, --cputick=1")
	dir      = flag.String("dir", "/var/log/tencloud-agent/", "dir is the directory to save dir, --dir=/var/log/tencloud-agent/")
	debug    = flag.Bool("debug", true, "debug is to distinguish environment, --debug=true")
)

// floatRound 浮点数截取x位，并保持类型不变
func floatRound(orig float64) (result float64) {
	tmp := strconv.FormatFloat(orig, 'f', PRECISION, 64)
	result, err := strconv.ParseFloat(tmp, 64)
	if err != nil {
		log.Println(err)
	}
	return
}

type agent struct {
	addr    string
	cputick time.Duration
	debug   bool
	logger  *log.Logger
}

type Stat struct {
	IP         string                 `json:"public_ip"`
	Time       int64                  `json:"time"`
	CPU        *CPUStat               `json:"cpu"`
	Mem        *MemStat               `json:"memory"`
	Disk       *DiskStat              `json:"disk"`
	Net        *NetStat               `json:"net"`
	SystemLoad *SystemLoad            `json:"system_load"`
	Docker     map[string]*DockerStat `json:"docker"`
	K8sNode    string                 `json:"k8s_node"`
	K8sDeploy  string                 `json:"k8s_deployment"`
	K8sRS      string                 `json:"k8s_replicaset"`
	K8sPod     string                 `json:"k8s_pod"`
	K8sService string                 `json:"k8s_service"`
}

type IPInfo struct {
	IP          string  `json:"query"`
	City        string  `json:"city"`
	Region      string  `json:"region"`
	RegionName  string  `json:"regionName"`
	Country     string  `json:"country"`
	CountryCode string  `json:"countryCode"`
	Timezone    string  `json:"timezone"`
	Lon         float64 `json:"lon"`
	Lat         float64 `json:"lat"`
	Org         string  `json:"org"`
	Isp         string  `json:"isp"`
	AS          string  `json:"as"`
}

func (a *agent) getPublicIP() (string, error) {
	resp, err := http.Get(PublicIP)
	if err != nil {
		return "", err
	}
	body, err := ioutil.ReadAll(resp.Body)
	defer resp.Body.Close()
	if err != nil {
		return "", err
	}
	var info *IPInfo
	err = json.Unmarshal(body, &info)
	if err != nil {
		return "", err
	}
	return info.IP, nil
}

// suporrt pipe operation
func (a *agent) osComand(obj string) (string, error) {
	cmd := exec.Command("/bin/sh", "-c", obj)
	var (
		out, cerr bytes.Buffer
	)
	out_w := bufio.NewWriter(&out)
	err_w := bufio.NewWriter(&cerr)
	cmd.Stdout = out_w
	cmd.Stderr = err_w
	cmd.Start()
	cmd.Run()
	cmd.Wait()
	out_w.Flush()
	err_w.Flush()

	if len(cerr.String()) != 0 {
		return "", errors.New(cerr.String())
	}
	return out.String(), nil
}

type CPUStat struct {
	Percent float64 `json:"percent"`
}

func (a *agent) getCPUStat() (*CPUStat, error) {
	cmd := `sar -P ALL 1 1|grep Average|grep all|awk '{print $8}'`
	out, err := a.osComand(cmd)
	if err != nil {
		return nil, err
	}
	out = strings.TrimSuffix(out, "\n")
	idle, err := strconv.ParseFloat(out, 64)
	if err != nil {
		return nil, err
	}
	usage := floatRound(float64(100) - idle)
	resp := &CPUStat{
		Percent: usage,
	}
	return resp, nil
}

type MemStat struct {
	MemPercent float64 `json:"percent"`
	Free       uint64  `json:"free"`
	Available  uint64  `json:"available"`
	Total      uint64  `json:"total"`
}

func (a *agent) getMemStat() (*MemStat, error) {
	resp := &MemStat{}
	memory, err := mem.VirtualMemory()
	if err != nil {
		return nil, err
	}
	resp.MemPercent = floatRound(float64(memory.UsedPercent))
	// bytes
	resp.Available = memory.Available
	resp.Free = memory.Free
	resp.Total = memory.Total
	return resp, nil
}

type DiskStat struct {
	DiskPercent float64 `json:"percent"`
	Total       uint64  `json:"total"`
	Free        uint64  `json:"free"`
	Utilize     float64 `json:"utilize"`
}

func (a *agent) getIOverage() (float64, error) {
	cmd := `sar -pd 1 1|grep Average |awk '{print $10}'`
	out, err := a.osComand(cmd)
	if err != nil {
		return 0.0, err
	}

	var (
		utlize []float64
		total  float64
	)
	for _, v := range strings.Split(out, "\n") {
		if len(v) == 0 {
			continue
		}
		u, err := strconv.ParseFloat(v, 64)
		if err != nil {
			continue
		}
		total += u
		utlize = append(utlize, u)
	}
	l := len(utlize)
	resp := floatRound(total / float64(l))
	return resp, nil
}

func (a *agent) getDiskStat() (*DiskStat, error) {
	resp := &DiskStat{}
	block, err := disk.Usage("/")
	if err != nil {
		return nil, err
	}
	utlize, err := a.getIOverage()
	if err != nil {
		return nil, err
	}
	resp.DiskPercent = floatRound(block.UsedPercent)
	resp.Free = block.Free
	resp.Total = block.Total
	resp.Utilize = utlize
	return resp, nil
}

type NetStat struct {
	Input  uint64 `json:"input"`
	Output uint64 `json:"output"`
}

func (a *agent) getNetStat() (*NetStat, error) {
	resp := &NetStat{}
	start, err := net.IOCounters(PERNIC)
	if err != nil {
		return nil, err
	}
	startRecv := start[0].BytesRecv
	startSent := start[0].BytesSent
	time.Sleep(10 * time.Second)
	end, err := net.IOCounters(PERNIC)
	if err != nil {
		return nil, err
	}
	endRecv := end[0].BytesRecv
	endSent := end[0].BytesSent
	recv := (endRecv - startRecv) / 10
	sent := (endSent - startSent) / 10
	// 转为kB
	resp.Input = (recv * 8) / kB
	resp.Output = (sent * 8) / kB
	return resp, nil
}

type DockerStat struct {
	Name        string  `json:"name"`
	PID         string  `json:"pid"`
	Container   string  `json:"container"`
	CPU         float64 `json:"cpu"`
	Memory      float64 `json:"mem_percent"`
	MemLimit    uint64  `json:"mem_limit"`
	MemUsage    uint64  `json:"mem_usage"`
	NetInput    uint64  `json:"net_input"`
	NetOutput   uint64  `json:"net_output"`
	BlockInput  uint64  `json:"block_input"`
	BlockOutput uint64  `json:"block_output"`
}

// 	arg3 = "{{.Name}},{{.Container}},{{.PIDs}}{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}}, {{.BlockIO}},{{.NetIO}}
func (a *agent) dealDockerStat(orig string) *DockerStat {

	transUnit := func(i []string) (resp uint64) {
		if strings.Contains(i[1], "KiB") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI * KiB)
		} else if strings.Contains(i[1], "MiB") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI * MiB)
		} else if strings.Contains(i[1], "GiB") {
			numI, _ := strconv.ParseFloat(i[1], 64)
			resp = uint64(numI * GiB)
		} else if strings.Contains(i[1], "kB") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI * kB)
		} else if strings.Contains(i[1], "MB") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI * MB)
		} else if strings.Contains(i[1], "GB") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI * GB)
		} else if strings.Contains(i[1], "B") {
			numI, _ := strconv.ParseFloat(i[0], 64)
			resp = uint64(numI)
		} else {
			a.logger.Println("unidentified unit")
		}
		return
	}

	origArray := []string{}
	for _, v := range strings.Split(orig, ",") {
		origArray = append(origArray, strings.TrimSpace(v))
	}
	dockerStat := &DockerStat{}
	dockerStat.Name = origArray[0]
	dockerStat.Container = origArray[1]
	dockerStat.PID = origArray[2]
	dockerStat.CPU, _ = strconv.ParseFloat(strings.Split(origArray[3], "%")[0], 64)
	dockerStat.Memory, _ = strconv.ParseFloat(strings.Split(origArray[4], "%")[0], 64)

	memory := strings.Split(origArray[5], "/")
	tmpUsage := strings.Split(strings.TrimSpace(memory[0]), " ")
	tmpLimit := strings.Split(strings.TrimSpace(memory[1]), " ")
	dockerStat.MemUsage = transUnit(tmpUsage)
	dockerStat.MemLimit = transUnit(tmpLimit)

	block := strings.Split(origArray[6], "/")
	tmpInput := strings.Split(strings.TrimSpace(block[0]), " ")
	tmpOutput := strings.Split(strings.TrimSpace(block[1]), " ")
	dockerStat.BlockInput = transUnit(tmpInput)
	dockerStat.BlockOutput = transUnit(tmpOutput)

	netStat := strings.Split(origArray[7], "/")
	tmpNetInput := strings.Split(strings.TrimSpace(netStat[0]), " ")
	tmpNetOutput := strings.Split(strings.TrimSpace(netStat[1]), " ")
	dockerStat.NetInput = transUnit(tmpNetInput)
	dockerStat.NetOutput = transUnit(tmpNetOutput)

	return dockerStat
}
func (a *agent) getDocketStat() (map[string]*DockerStat, error) {
	out, err := exec.Command(docker, stats, stream, format, pattern).Output()
	if err != nil {
		return nil, err
	}
	resp := map[string]*DockerStat{}
	for _, v := range bytes.Split(out, []byte("\n")) {
		if len(v) != 0 {
			docker := a.dealDockerStat(string(v))
			resp[docker.Name] = docker
		}
	}
	return resp, nil
}

type SystemLoad struct {
	SystemDate  string  `json:"date"`
	Runtime     string  `json:"run_time"`
	LoginUsers  int     `json:"login_users"`
	OneLoad     float64 `json:"one_minute_load"`
	FiveLoad    float64 `json:"five_minute_load"`
	FifteenLoad float64 `json:"fifth_minute_load"`
}

func (a *agent) getSystemLoad() (*SystemLoad, error) {
	resp := &SystemLoad{}
	date, err := exec.Command("date", "+%Y-%m-%d %H:%M:%S").Output()
	if err != nil {
		return nil, err
	}
	resp.SystemDate = strings.TrimRight(string(date), "\n")

	loadStat, err := load.Avg()
	if err != nil {
		return nil, err
	}
	resp.OneLoad = loadStat.Load1
	resp.FiveLoad = loadStat.Load5
	resp.FifteenLoad = loadStat.Load15

	var runtime bytes.Buffer
	out, err := exec.Command(cat, uptime).Output()
	if err != nil {
		return nil, err
	}
	strSecond, err := strconv.ParseFloat(strings.TrimSpace(strings.Split(string(out), " ")[0]), 64)
	if err != nil {
		return nil, err
	}
	second := int64(strSecond)
	days := second / 86400
	hours := (second % 86400) / 3600
	minutes := (second % 3600) / 60
	sec := second % 60

	if days > 0 {
		d := fmt.Sprintf("%d天", days)
		runtime.WriteString(d)
	}
	if hours > 0 {
		h := fmt.Sprintf("%d小时", hours)
		runtime.WriteString(h)
	}
	if minutes > 0 {
		m := fmt.Sprintf("%d分钟", minutes)
		runtime.WriteString(m)
	}
	if sec > 0 {
		s := fmt.Sprintf("%d秒", sec)
		runtime.WriteString(s)
	}
	resp.Runtime = runtime.String()

	u, err := exec.Command("users").Output()
	if err != nil {
		return nil, err
	}
	resp.LoginUsers = len(strings.Split(string(u), " "))
	return resp, nil
}

func (a *agent) getK8sNodeInfo() (string, error) {
	out, err := exec.Command("kubectl", "get", "nodes", "-o", "yaml").Output()
	if err != nil {
		return "", err
	}

	if bytes.Contains(out, []byte("The connection to the server")) {
		return "", err
	}

	if bytes.Contains(out, []byte("No resources found.")) {
		return "", err
	}

	return string(out), nil
}

func (a *agent) getK8sResourceInfo(obj string) (string, error) {
	out, err := exec.Command("kubectl", "get", obj, "-o", "yaml").Output()
	if err != nil {
		return "", err
	}

	if bytes.Contains(out, []byte("The connection to the server")) {
		return "", err
	}

	if bytes.Contains(out, []byte("No resources found.")) {
		return "", err
	}

	if bytes.Contains(out, []byte("error: the server doesn't have a resource type")) {
		return "", err
	}

	return string(out), nil
}

func (a *agent) postData() {
	ip := DefaultIP
	if !a.debug {
		tip, err := a.getPublicIP()
		if err != nil {
			a.logger.Println(err)
		}
		ip = tip
	}
	cpu, err := a.getCPUStat()
	if err != nil {
		a.logger.Println(err)
		cpu = &CPUStat{}
	}
	mem, err := a.getMemStat()
	if err != nil {
		a.logger.Println(err)
		mem = &MemStat{}
	}
	disk, err := a.getDiskStat()
	if err != nil {
		a.logger.Println(err)
		disk = &DiskStat{}
	}
	net, err := a.getNetStat()
	if err != nil {
		a.logger.Println(err)
		net = &NetStat{}
	}
	load, err := a.getSystemLoad()
	if err != nil {
		a.logger.Println(err)
		load = &SystemLoad{}
	}
	docker, err := a.getDocketStat()
	if err != nil {
		a.logger.Println(err)
		docker = map[string]*DockerStat{}
	}
	k8s_node, err := a.getK8sNodeInfo()
	if err != nil {
		a.logger.Println(err)
		k8s_node = ""
	}

	k8s_deployment, err := a.getK8sResourceInfo("deployments")
	if err != nil {
		a.logger.Println(err)
		k8s_deployment = ""
	}

	k8s_replicaset, err := a.getK8sResourceInfo("replicasets")
	if err != nil {
		a.logger.Println(err)
		k8s_replicaset = ""
	}

	k8s_pod, err := a.getK8sResourceInfo("pods")
	if err != nil {
		a.logger.Println(err)
		k8s_pod = ""
	}

	k8s_service, err := a.getK8sResourceInfo("services")
	if err != nil {
		a.logger.Println(err)
		k8s_service = ""
	}

	stat := &Stat{
		IP:         ip,
		Time:       time.Now().Unix(),
		CPU:        cpu,
		Mem:        mem,
		Disk:       disk,
		Net:        net,
		SystemLoad: load,
		Docker:     docker,
		K8sNode:    k8s_node,
		K8sDeploy:  k8s_deployment,
		K8sRS:      k8s_replicaset,
		K8sPod:     k8s_pod,
		K8sService: k8s_service,
	}
	b, err := json.Marshal(stat)
	if err != nil {
		a.logger.Println(err)
		return
	}
	body := bytes.NewBuffer(b)
	resp, err := http.Post(
		a.addr,
		"application/json",
		body,
	)
	if err != nil {
		a.logger.Printf("failed to post data\n%+v \nerror: %s\n", stat, err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		a.logger.Printf("failed to post data\n%+v \nresp code is %d\n", stat, resp.StatusCode)
		return
	}
	a.logger.Printf("success to post data\n%+v\n", stat)
	return
}
func main() {
	flag.Parse()
	logf, _ := rotatelogs.New(
		*dir+"tencloud-agent.%Y%m%d",
		rotatelogs.WithMaxAge(LogAge),
		rotatelogs.WithRotationTime(LogRotate),
	)
	logger := log.New(logf, "", log.Ldate|log.Ltime|log.Llongfile)
	a := &agent{
		addr:    *addr,
		logger:  logger,
		debug:   *debug,
		cputick: time.Duration(*cputick),
	}
	startT := time.Now().Format(time.RFC3339)
	a.logger.Printf("start report data, %s\n", startT)
	a.postData()
	endT := time.Now().Format(time.RFC3339)
	a.logger.Printf("end report data, %s\n\n", endT)
	ticker := time.NewTicker(time.Duration(*interval) * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		T1 := time.Now().Format(time.RFC3339)
		a.logger.Printf("start report data, %s\n", T1)
		a.postData()
		T2 := time.Now().Format(time.RFC3339)
		a.logger.Printf("end report data, %s\n\n", T2)
	}
}
