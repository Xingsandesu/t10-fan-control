#!/bin/bash
# 构建 Docker 镜像
docker build -t gpu-fan-builder .

# 创建临时容器并复制构建产物
docker run -it --rm -v $(pwd):/app gpu-fan-builder

python3 -m nuitka \
    --mode=standalone \
    --onefile \
    --include-module=pynvml \
    --include-package=loguru \
    main.py

# 添加执行权限
chmod +x gpu-fan-control