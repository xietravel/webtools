#!/bin/sh

# 定义IPv6接口名称（根据实际情况修改）
IPV6_INTERFACE="wan6"

# 定义存储IPv4地址的文件路径
IPV4_ADDR_FILE="/tmp/ipv4_address.txt"

# 获取当前的IPv4地址（从4.ipw.cn）
CURRENT_IP=$(curl -s -4 --connect-timeout 5 4.ipw.cn 2>/dev/null)

# 检查是否成功获取到IPv4地址
if [ -z "$CURRENT_IP" ]; then
    echo "Failed to get IPv4 address from 4.ipw.cn"
    exit 1
fi

echo "Current IPv4 address from 4.ipw.cn: $CURRENT_IP"

# 检查是否存在存储的IPv4地址文件
if [ -f "$IPV4_ADDR_FILE" ]; then
    # 读取之前存储的IPv4地址
    STORED_IP=$(cat "$IPV4_ADDR_FILE")
    echo "Stored IPv4 address: $STORED_IP"
    
    # 比较当前地址和存储的地址
    if [ "$CURRENT_IP" != "$STORED_IP" ]; then
        echo "IPv4 address changed from $STORED_IP to $CURRENT_IP"
        echo "Restarting IPv6 interface $IPV6_INTERFACE..."
        
        # 存储新的IPv4地址
        echo "$CURRENT_IP" > "$IPV4_ADDR_FILE"
        
        # 重启IPv6接口
        ifdown $IPV6_INTERFACE
        sleep 2
        ifup $IPV6_INTERFACE
        
        echo "IPv6 interface $IPV6_INTERFACE restarted due to IPv4 address change."
    else
        echo "IPv4 address unchanged ($CURRENT_IP)."
    fi
else
    # 如果是第一次运行，存储当前IPv4地址
    echo "$CURRENT_IP" > "$IPV4_ADDR_FILE"
    echo "Initial IPv4 address stored: $CURRENT_IP"
fi