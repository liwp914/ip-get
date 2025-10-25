#!/bin/bash

# WebDAV配置 - 使用环境变量增强安全性
WEBDAV_URL="${WEBDAV_URL}"
USERNAME="${WEBDAV_USERNAME}"
PASSWORD="${WEBDAV_PASSWORD}"

# 设置脚本错误时退出
set -e

echo "开始WebDAV上传过程..."
echo "WebDAV URL: $WEBDAV_URL"

# 检查output目录是否存在
if [ ! -d "output" ]; then
    echo "错误：output目录不存在"
    exit 1
fi

# 进入output目录
cd output || exit 1

# 获取所有文件列表
shopt -s nullglob
files=( * )
if [ ${#files[@]} -eq 0 ]; then
    echo "错误：output目录为空"
    exit 1
fi

# 统计变量
total_files=${#files[@]}
success_count=0
fail_count=0
failed_files=()

# 遍历上传文件
for file in "${files[@]}"; do
    if [ -d "$file" ]; then
        echo "跳过目录: $file"
        continue
    fi
    
    echo "正在上传: $file"
    
    # 执行上传操作
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X PUT "${WEBDAV_URL}/${file}" \
        --user "${USERNAME}:${PASSWORD}" \
        -T "$file")
    
    # 结果判断
    case $http_code in
        201|204)
            echo "✓ 上传成功: $file"
            ((success_count++))
            ;;
        409)
            echo "⚠ 冲突错误（文件可能已存在）: $file"
            ((fail_count++))
            failed_files+=("$file")
            ;;
        401)
            echo "✗ 认证失败，请检查账号密码"
            exit 2
            ;;
        *)
            echo "✗ 上传失败 (HTTP $http_code): $file"
            ((fail_count++))
            failed_files+=("$file")
            ;;
    esac
done

# 返回原目录
cd ..

# 输出统计结果
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━"
echo "上传统计:"
echo "文件总数 : $total_files"
echo "成功上传 : $success_count"
echo "失败数量 : $fail_count"

if [ $fail_count -gt 0 ]; then
    echo "失败的文件:"
    printf '%s\n' "${failed_files[@]}"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━"
echo "WebDAV上传完成 ✓"