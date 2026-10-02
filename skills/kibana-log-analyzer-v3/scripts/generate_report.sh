#!/bin/bash
# 生成汇总报告
# 用法: ./generate_report.sh <output_file> <group_reports_dir>

OUTPUT_FILE="${1:-kibana-error-report-$(date +%Y%m%d-%H%M%S).md}"
REPORTS_DIR="${2:-./reports}"

# 创建输出目录
mkdir -p "$(dirname "$OUTPUT_FILE")"

# 读取模板
TEMPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)/assets"
TEMPLATE="$TEMPLATE_DIR/report_template.md"

if [ ! -f "$TEMPLATE" ]; then
  echo "Error: Template not found at $TEMPLATE"
  exit 1
fi

# 统计全局信息
TOTAL_ERRORS=0
APP_COUNT=0
GROUP_COUNT=0

# 收集所有分组报告
GROUP_REPORTS=""
SEVERITY_P0=0
SEVERITY_P1=0
SEVERITY_P2=0
SEVERITY_P3=0

for report in "$REPORTS_DIR"/*.md; do
  if [ -f "$report" ]; then
    GROUP_REPORTS="${GROUP_REPORTS}$(cat "$report")\n\n---\n\n"
    GROUP_COUNT=$((GROUP_COUNT + 1))
    
    # 统计影响等级
    if grep -q "\[P0\]" "$report"; then
      SEVERITY_P0=$((SEVERITY_P0 + 1))
    elif grep -q "\[P1\]" "$report"; then
      SEVERITY_P1=$((SEVERITY_P1 + 1))
    elif grep -q "\[P2\]" "$report"; then
      SEVERITY_P2=$((SEVERITY_P2 + 1))
    elif grep -q "\[P3\]" "$report"; then
      SEVERITY_P3=$((SEVERITY_P3 + 1))
    fi
  fi
done

# 替换模板变量
sed -e "s/{{timestamp}}/$(date '+%Y-%m-%d %H:%M:%S')/g" \
    -e "s/{{time_range}}/最近 1 小时/g" \
    -e "s/{{total_errors}}/$TOTAL_ERRORS/g" \
    -e "s/{{app_count}}/$APP_COUNT/g" \
    -e "s/{{group_count}}/$GROUP_COUNT/g" \
    "$TEMPLATE" > "$OUTPUT_FILE"

echo "Report generated: $OUTPUT_FILE"
echo "Total groups: $GROUP_COUNT"
echo "Severity distribution: P0=$SEVERITY_P0, P1=$SEVERITY_P1, P2=$SEVERITY_P2, P3=$SEVERITY_P3"
