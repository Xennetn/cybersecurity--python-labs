#!/usr/bin/env bash
# Сценарії 2-13 із завдання 3 (варіант 9). Запускати при працюючому API:
#   bash labs/lab03/demo_requests.sh
# Сценарії 1 (seed) і 14 (перезапуск сервера) виконуються вручну.
BASE="${BASE:-http://127.0.0.1:8000}"
JSON_HEADER='Content-Type: application/json'
RESP="$(mktemp)"
trap 'rm -f "$RESP"' EXIT

count() {
  curl -s "$BASE/records?limit=100" |
    python3 -c 'import json,sys; print(len(json.load(sys.stdin)))'
}

call() { # call МЕТОД ШЛЯХ [ТІЛО]
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    echo "\$ curl -X $method \"$BASE$path\" -d '$body'"
    curl -s -o "$RESP" -w "HTTP %{http_code}\n" -X "$method" "$BASE$path" \
      -H "$JSON_HEADER" -d "$body"
  else
    echo "\$ curl -X $method \"$BASE$path\""
    curl -s -o "$RESP" -w "HTTP %{http_code}\n" -X "$method" "$BASE$path"
  fi
  if [ -s "$RESP" ]; then cat "$RESP"; echo; fi
  echo
}

title() { echo "=================== $1 ==================="; }

CODE="V09-T$RANDOM"
NEW="{\"code\":\"$CODE\",\"title\":\"Навчальне вимірювання\",\"category_id\":1,\"value\":7.5,\"status\":\"new\"}"

title "Сценарій 2: /ping, /student, /categories"
call GET /ping
call GET /student
call GET /categories

title "Сценарій 3: повний цикл CRUD"
call POST /records "$NEW"
RID=$(python3 -c "import json; print(json.load(open('$RESP'))['id'])")
call GET "/records/$RID"
call PUT "/records/$RID" "{\"code\":\"$CODE-U\",\"title\":\"Оновлене вимірювання\",\"category_id\":2,\"value\":20,\"status\":\"done\"}"
call DELETE "/records/$RID"
call GET "/records/$RID"

title "Сценарій 4: фільтри, limit і offset"
call GET "/records?category_id=1"
call GET "/records?status=done"
call GET "/records?min_value=15"
call GET "/records?category_id=1&status=done&min_value=10"
call GET "/records?limit=3&offset=2"

title "Сценарій 5: помилки перевірки (422), база не змінюється"
BEFORE=$(count); echo "Записів до: $BEFORE"; echo
call POST /records '{"code":"V09-BAD1","title":"Від'"'"'ємне значення","category_id":1,"value":-1,"status":"new"}'
call POST /records '{"code":"V09-BAD2","title":"   ","category_id":1,"value":5,"status":"new"}'
call POST /records '{"code":"V09-BAD3","title":"Поганий статус","category_id":1,"value":5,"status":"bogus"}'
call GET "/records?limit=0"
echo "Записів після: $(count)"; echo

title "Сценарій 6: неправильний тип value (верхньої межі немає)"
call POST /records '{"code":"V09-BAD4","title":"Рядок замість числа","category_id":1,"value":"abc","status":"new"}'
call POST /records '{"code":"V09-BAD5","title":"Булеве значення","category_id":1,"value":true,"status":"new"}'
call GET "/records?min_value=inf"

title "Сценарій 7: 404"
call GET /records/99999
call POST /records '{"code":"V09-NOCAT","title":"Неіснуюча категорія","category_id":99,"value":5,"status":"new"}'

title "Сценарій 8: 409 (дублікати)"
call POST /records '{"code":"V09-01","title":"Дублікат коду","category_id":1,"value":5,"status":"new"}'
call POST /categories '{"name":"siem"}'

title "Сценарій 9: видалення категорій"
call DELETE /categories/1
call POST /categories "{\"name\":\"tmp$RANDOM\"}"
CID=$(python3 -c "import json; print(json.load(open('$RESP'))['id'])")
call DELETE "/categories/$CID"

title "Сценарій 10: коректний пакет із двох записів"
call POST /records/bulk "[{\"code\":\"$CODE-B1\",\"title\":\"Пакет перший\",\"category_id\":1,\"value\":4.0,\"status\":\"new\"},{\"code\":\"$CODE-B2\",\"title\":\"Пакет другий\",\"category_id\":2,\"value\":5.0,\"status\":\"done\"}]"

title "Сценарій 11: пакет із дублікатом code з бази (відкат)"
BEFORE=$(count); echo "Записів до: $BEFORE"; echo
call POST /records/bulk '[{"code":"V09-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V09-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
echo "Записів після: $(count)"
echo "Пошук V09-ROLLBACK за title:"
curl -s -G "$BASE/records" --data-urlencode "q=Перший елемент"; echo; echo

title "Сценарій 12: пакет із неіснуючою категорією (відкат)"
BEFORE=$(count); echo "Записів до: $BEFORE"; echo
call POST /records/bulk '[{"code":"V09-ROLLBACK2","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V09-NOCAT2","title":"Неіснуюча категорія","category_id":99,"value":5.0,"status":"new"}]'
echo "Записів після: $(count)"; echo

title "Сценарій 13: SQL-ін'єкція в параметрі q"
BEFORE=$(count); echo "Записів до: $BEFORE"
echo "\$ curl -G \"$BASE/records\" --data-urlencode \"q=' OR 1=1 --\""
curl -s -G "$BASE/records" --data-urlencode "q=' OR 1=1 --" -w "\nHTTP %{http_code}\n"
echo "Записів після: $(count)"
