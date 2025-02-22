# t10-fan-control
# GPU 风扇智能控制程序

这是一个用于 NVIDIA T10 GPU 的智能风扇控制程序,可以根据 GPU 温度自动调节风扇转速。

## 特性

- 全线性温控算法
- 低温静音运行(25℃以下 30%转速)
- 高温全速保护(60℃以上 100%转速) 
- 优化的整数计算,资源占用极低
- 支持 systemd 服务自动启动
- 详细的日志记录和异常处理
- 优雅的程序退出恢复默认设置

## 依赖

```bash
pip install pynvml loguru
```

## 使用方法

### 直接运行

- 其实直接从Actions里面下载编译好的二进制就可以运行了

```bash
python main.py /sys/class/hwmon/hwmon1/pwm1
```

参数说明:
- `pwm_path`: 风扇 PWM 控制文件路径(必需)
- `--interval`: 检测间隔,默认 2 秒

### Systemd 服务安装(Linux)

1. 复制程序到指定位置:
```bash
sudo mkdir -p /opt/gpu-fan-control
sudo cp main.py /opt/gpu-fan-control/
```

2. 创建服务文件:
```bash
sudo cp gpu-fan-control.service /etc/systemd/system/
```

3. 启用并启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gpu-fan-control
sudo systemctl start gpu-fan-control
```


## 配置说明

- MIN_TEMP = 25 # 最低温度阈值
- MAX_TEMP = 60 # 最高温度阈值
- MIN_SPEED = 77 # 最低转速(30%)
- MAX_SPEED = 255 # 最高转速(100%)

## 日志

- 控制台输出: 彩色实时日志
- 文件日志: gpu_fan.log
  - 自动轮转(超过 10MB)
  - 保留一周日志

## 故障排除

1. 找不到 PWM 控制文件
   - 检查文件路径是否正确
   - 确认用户权限

2. 无法读取 GPU 温度
   - 检查 NVIDIA 驱动是否正确安装
   - 确认 NVML 库可用

## 许可证

MIT License
