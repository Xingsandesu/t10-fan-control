from pynvml import (
    nvmlInit,
    nvmlShutdown,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetTemperature,
    NVML_TEMPERATURE_GPU,
    NVMLError,
    nvmlDeviceGetCount,
    nvmlDeviceGetName,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetPowerUsage,
    nvmlDeviceGetFanSpeed
)
from loguru import logger
import argparse
import time
import os
import sys

# 配置日志记录
logger.remove()  # 移除默认处理程序
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

def get_gpu_temp():
    """获取 GPU 温度"""
    try:
        return nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
    except NVMLError as e:
        logger.error(f"无法读取 GPU 温度: {e}")
        return 0

def set_fan_speed(pwm_path, speed):
    """设置风扇转速 (0-255)"""
    try:
        speed = max(0, min(255, int(speed)))  # 确保速度在有效范围内
        with open(pwm_path, 'w') as f:
            f.write(str(speed))
    except (IOError, OSError) as e:
        logger.error(f"无法写入风扇控制文件 {pwm_path}: {e}")
    except Exception as e:
        logger.error(f"设置风扇转速时发生未知错误: {e}")

def calculate_fan_speed(temp):
    """根据温度计算风扇转速的全线性版本
    - 25℃及以下时保持最低速度 30% (PWM=77)
    - 25-60℃时完全线性增加
    - 60℃及以上时保持最高速度 100% (PWM=255)
    """
    MIN_TEMP = 25
    MAX_TEMP = 60
    MIN_SPEED = 77   # 30% 最低速度
    MAX_SPEED = 255  # 100% 最高速度
    
    if temp <= MIN_TEMP:
        return MIN_SPEED
    if temp >= MAX_TEMP:
        return MAX_SPEED
        
    # 使用精确的整数运算公式
    return ((temp - MIN_TEMP) * (MAX_SPEED - MIN_SPEED)) // (MAX_TEMP - MIN_TEMP) + MIN_SPEED

def print_gpu_info():
    """打印所有GPU的详细信息"""
    try:
        nvmlInit()
        deviceCount = nvmlDeviceGetCount()
        logger.info(f"系统中发现 {deviceCount} 个 GPU 设备:")
        
        for i in range(deviceCount):
            handle = nvmlDeviceGetHandleByIndex(i)
            
            # 获取基本信息
            name = nvmlDeviceGetName(handle)
            temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
            
            # 获取内存信息
            memory = nvmlDeviceGetMemoryInfo(handle)
            memory_total = memory.total / 1024**2  # 转换为MB
            memory_used = memory.used / 1024**2
            memory_free = memory.free / 1024**2
            
            # 获取功耗信息（可能某些GPU不支持）
            try:
                power = nvmlDeviceGetPowerUsage(handle) / 1000.0  # 转换为瓦特
            except NVMLError:
                power = None
                
            # 获取风扇转速（可能某些GPU不支持）
            try:
                fan = nvmlDeviceGetFanSpeed(handle)
            except NVMLError:
                fan = None
            
            logger.info(f"\nGPU {i}: {name}")
            logger.info(f"温度: {temp}°C")
            logger.info(f"显存: 已用 {memory_used:.0f}MB / 总共 {memory_total:.0f}MB (剩余 {memory_free:.0f}MB)")
            if power is not None:
                logger.info(f"功耗: {power:.1f}W")
            if fan is not None:
                logger.info(f"风扇转速: {fan}%")
                
    except NVMLError as e:
        logger.error(f"获取GPU信息时出错: {e}")
    finally:
        nvmlShutdown()

    
def main():
    parser = argparse.ArgumentParser(description='GPU 风扇控制程序')
    parser.add_argument('pwm_path', nargs='?', help='风扇 PWM 控制文件路径')
    parser.add_argument('--interval', type=float, default=2.0, help='检查间隔(秒)')
    parser.add_argument('--info', action='store_true', help='显示GPU详细信息后退出')
    args = parser.parse_args()
    
    if args.info:
        print_gpu_info()
        return 0
    
    if not args.pwm_path:
        parser.error("需要提供 PWM 控制文件路径，除非使用 --info 选项")

    # 验证PWM文件路径
    if not os.path.exists(args.pwm_path):
        logger.error(f"PWM控制文件不存在: {args.pwm_path}")
        return 1
    
    if args.interval < 0.1:
        logger.warning("检查间隔过短可能导致系统负载过高")
        args.interval = 0.1

    try:
        nvmlInit()
        global handle
        handle = nvmlDeviceGetHandleByIndex(0)
        
        # 确保程序退出时恢复默认风扇速度
        def cleanup():
            try:
                set_fan_speed(args.pwm_path, 77)  # 恢复到30%的默认速度
                nvmlShutdown()
            except:
                pass
                
        import atexit
        atexit.register(cleanup)
        
        logger.info(f"正在监控 GPU 温度，使用 PWM 路径: {args.pwm_path}")
        
        while True:
            temp = get_gpu_temp()
            if temp > 0:
                speed = calculate_fan_speed(temp)
                set_fan_speed(args.pwm_path, speed)
                logger.info(f"温度: {temp}°C, 风扇转速: {int(speed)}/255 ({int(speed/255*100)}%)")
            else:
                logger.warning("无法获取GPU温度，使用默认转速")
                set_fan_speed(args.pwm_path, 77)
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logger.info("程序已停止")
    except Exception as e:
        logger.exception("程序发生错误")
        return 1
    finally:
        cleanup()
    return 0

if __name__ == "__main__":
    main()
