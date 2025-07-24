#!/bin/bash

# 综合测试脚本：图片生成、视频生成、任务查询

BASE_URL="http://localhost:5511"
API_KEY="sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY"

echo "=================================="
echo "    Kling API 综合功能测试"
echo "=================================="
echo "服务地址: $BASE_URL"
echo "API密钥: ${API_KEY:0:20}..."
echo ""

# 1. 测试图片生成
echo "🎨 1. 测试图片生成..."
echo "----------------------------------"

IMAGE_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A majestic dragon flying over a mystical forest at sunset, fantasy art style",
    "aspect_ratio": "16:9",
    "cfg_scale": 0.7,
    "negative_prompt": "blurry, low quality"
  }' \
  "$BASE_URL/api/images/generations")

echo "图片生成请求响应:"
echo "$IMAGE_RESPONSE" | jq .

# 提取图片任务ID
IMAGE_TASK_ID=$(echo "$IMAGE_RESPONSE" | jq -r '.data.data.task_id // empty')
echo ""
echo "📝 图片任务ID: $IMAGE_TASK_ID"
echo ""

# 2. 测试视频生成
echo "🎬 2. 测试视频生成..."
echo "----------------------------------"

VIDEO_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A time-lapse of clouds moving across a blue sky with birds flying",
    "aspect_ratio": "16:9",
    "duration": 5,
    "cfg_scale": 0.5
  }' \
  "$BASE_URL/api/videos/text-to-video")

echo "视频生成请求响应:"
echo "$VIDEO_RESPONSE" | jq .

# 提取视频任务ID
VIDEO_TASK_ID=$(echo "$VIDEO_RESPONSE" | jq -r '.data.data.task_id // empty')
echo ""
echo "📝 视频任务ID: $VIDEO_TASK_ID"
echo ""

# 3. 测试任务查询
echo "🔍 3. 测试任务查询..."
echo "----------------------------------"

# 等待2秒让任务开始处理
echo "⏱️  等待任务开始处理..."
sleep 2

if [ -n "$IMAGE_TASK_ID" ] && [ "$IMAGE_TASK_ID" != "null" ]; then
    echo ""
    echo "🖼️  查询图片任务状态..."
    curl -s -X GET \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/tasks/$IMAGE_TASK_ID/status?task_type=text_to_image" | jq .
    
    echo ""
    echo "🖼️  查询图片任务完整信息..."
    curl -s -X GET \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/tasks/$IMAGE_TASK_ID?task_type=text_to_image" | jq .
else
    echo "❌ 图片任务ID无效，跳过图片任务查询"
fi

echo ""

if [ -n "$VIDEO_TASK_ID" ] && [ "$VIDEO_TASK_ID" != "null" ]; then
    echo "🎬 查询视频任务状态..."
    curl -s -X GET \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/tasks/$VIDEO_TASK_ID/status?task_type=text_to_video" | jq .
    
    echo ""
    echo "🎬 查询视频任务完整信息..."
    curl -s -X GET \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/tasks/$VIDEO_TASK_ID?task_type=text_to_video" | jq .
else
    echo "❌ 视频任务ID无效，跳过视频任务查询"
fi

echo ""
echo "=================================="
echo "           测试完成"
echo "=================================="

# 4. 额外测试：任务类型自动检测
if [ -n "$IMAGE_TASK_ID" ] && [ "$IMAGE_TASK_ID" != "null" ]; then
    echo ""
    echo "🔍 4. 测试任务类型自动检测..."
    echo "----------------------------------"
    echo "不指定任务类型，让系统自动检测："
    curl -s -X GET \
      -H "Authorization: Bearer $API_KEY" \
      "$BASE_URL/api/tasks/$IMAGE_TASK_ID/status" | jq .
fi

echo ""
echo "✅ 所有测试完成！"