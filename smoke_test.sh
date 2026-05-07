#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-smoke$(date +%s)@test.com}"
PASSWORD="${PASSWORD:-SecurePass123!}"
NAME="${NAME:-Smoke User}"

echo "==> Base URL: ${BASE_URL}"
echo "==> Test email: ${EMAIL}"

register_payload=$(cat <<EOF
{"name":"${NAME}","email":"${EMAIL}","password":"${PASSWORD}"}
EOF
)

register_res=$(curl -sS -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "${register_payload}")
echo "==> Register response: ${register_res}"

login_payload=$(cat <<EOF
{"email":"${EMAIL}","password":"${PASSWORD}"}
EOF
)

token=$(curl -sS -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "${login_payload}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "==> Login token received"

auth_header="Authorization: Bearer ${token}"

me_res=$(curl -sS "${BASE_URL}/auth/me" -H "${auth_header}")
echo "==> /auth/me: ${me_res}"

business_payload='{"name":"Smoke Salon","category":"Salon","location":"Nairobi"}'
business_res=$(curl -sS -X POST "${BASE_URL}/business/" \
  -H "Content-Type: application/json" \
  -H "${auth_header}" \
  -d "${business_payload}")
business_id=$(echo "${business_res}" | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "==> Business created: ${business_res}"

sale_payload=$(cat <<EOF
{"business_id":${business_id},"amount":2500,"notes":"Smoke sale"}
EOF
)
sale_res=$(curl -sS -X POST "${BASE_URL}/sales/" \
  -H "Content-Type: application/json" \
  -H "${auth_header}" \
  -d "${sale_payload}")
echo "==> Sale created: ${sale_res}"

stock_payload=$(cat <<EOF
{"business_id":${business_id},"item_name":"Shampoo 500ml","quantity":20,"cost_price":180,"selling_price":250,"low_stock_threshold":5}
EOF
)
stock_res=$(curl -sS -X POST "${BASE_URL}/stock/" \
  -H "Content-Type: application/json" \
  -H "${auth_header}" \
  -d "${stock_payload}")
echo "==> Stock item created: ${stock_res}"

due_date=$(date -I -d "+2 days")
reminder_payload=$(cat <<EOF
{"business_id":${business_id},"type":"permit","message":"Permit renewal due","due_date":"${due_date}"}
EOF
)
reminder_res=$(curl -sS -X POST "${BASE_URL}/reminders/" \
  -H "Content-Type: application/json" \
  -H "${auth_header}" \
  -d "${reminder_payload}")
echo "==> Reminder created: ${reminder_res}"

summary_res=$(curl -sS "${BASE_URL}/sales/summary?business_id=${business_id}&period=today" -H "${auth_header}")
echo "==> Sales summary: ${summary_res}"

echo "==> Smoke test completed successfully."
