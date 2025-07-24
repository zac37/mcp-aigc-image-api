#!/bin/bash

# 测试Kling API修复的curl验证脚本

BASE_URL="http://localhost:5511"  # FastAPI服务地址
TEST_API_KEY="sk-idDBqyoDVqCXInnO9uaGLUfwsxY7RhzHSn166z5jOBCBvFmY"   # 真实API密钥
TEST_TASK_ID="776694602832805961" # 真实任务ID

echo "=== 测试Kling API任务查询修复 ==="
echo "服务地址: $BASE_URL"
echo "测试API密钥: $TEST_API_KEY"
echo "测试任务ID: $TEST_TASK_ID"
echo ""

# 1. 测试健康检查
echo "1. 测试健康检查..."
curl -s -X GET "$BASE_URL/api/health" | jq .
echo ""

# 2. 测试任务状态查询（不指定类型）
echo "2. 测试任务状态查询（自动检测类型）..."
curl -s -X GET \
  -H "Authorization: Bearer $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID/status" | jq .
echo ""

# 3. 测试任务状态查询（指定text_to_image类型）
echo "3. 测试任务状态查询（指定text_to_image类型）..."
curl -s -X GET \
  -H "Authorization: Bearer $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID/status?task_type=text_to_image" | jq .
echo ""

# 4. 测试任务结果查询（指定text_to_video类型）
echo "4. 测试任务结果查询（指定text_to_video类型）..."
curl -s -X GET \
  -H "Authorization: Bearer $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID/result?task_type=text_to_video" | jq .
echo ""

# 5. 测试完整任务信息查询（指定image_to_video类型）
echo "5. 测试完整任务信息查询（指定image_to_video类型）..."
curl -s -X GET \
  -H "Authorization: Bearer $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID?task_type=image_to_video" | jq .
echo ""

# 6. 测试无效任务类型
echo "6. 测试无效任务类型..."
curl -s -X GET \
  -H "Authorization: Bearer $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID/status?task_type=invalid_type" | jq .
echo ""

# 7. 测试无Authorization头部
echo "7. 测试无Authorization头部..."
curl -s -X GET \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/tasks/$TEST_TASK_ID/status" | jq .
echo ""

echo "=== 测试完成 ==="