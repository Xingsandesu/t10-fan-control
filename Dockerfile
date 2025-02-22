FROM quay.io/pypa/manylinux_2_34_x86_64

# 安装 Python 和 pip
RUN yum update -y && \
    yum install -y python3 python3-pip python-devel && \
    yum clean all

# 安装 Python 依赖
COPY requirements.txt /app/requirements.txt
WORKDIR /app

# 安装依赖
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

# 复制源代码
COPY . /app/

# 设置默认命令为 bash
CMD ["/bin/bash"]