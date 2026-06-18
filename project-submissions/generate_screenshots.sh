#!/usr/bin/env bash
# Generate terminal screenshots for each project tutorial
# Requires: python3, script (part of bsdutils)
# Run from project-submissions/ directory

set -e

SCREENSHOTS_DIR="$(dirname "$0")"

run_and_capture() {
    local project="$1"
    local cmd="$2"
    local output="$3"
    echo "=== Running $project demo ==="
    eval "$cmd" > "/tmp/${project}_demo.txt" 2>&1
    # Create a styled screenshot using ANSI-to-HTML or just keep as text
    cp "/tmp/${project}_demo.txt" "${SCREENSHOTS_DIR}/${project}/assets/screenshot-1.txt"
    echo "  Captured to ${project}/assets/screenshot-1.txt"
}

# Expense Tracker
run_and_capture "expense-tracker" \
    "cd ${SCREENSHOTS_DIR}/expense-tracker/solution && python3 -c \"
from models import Transaction
from database import init_db, insert_transaction, get_monthly_summary
init_db()
t = Transaction(amount=25.50, category='Food', date='2025-01-15', note='Lunch')
insert_transaction(t)
summary = get_monthly_summary(2025, 1)
for s in summary:
    print(f'  {s[\"category\"]}: \${s[\"total\"]:.2f}')
print('Expense Tracker: OK')
\"" 2>&1 | head -20

# Chat Server - test protocol
run_and_capture "chat-server" \
    "cd ${SCREENSHOTS_DIR}/chat-server/solution && python3 -c \"
from protocol import encode, decode, Message
msg = Message(type='MSG', sender='alice', body='Hello!', room='general')
data = encode(msg)
print('Raw:', repr(data[:50]))
decoded = decode(data)
print(f'Sent: {msg}')
print(f'Recv: {decoded}')
print('Chat Protocol: OK')
\"" 2>&1 | head -20

# API Framework - test routes
run_and_capture "api-framework" \
    "cd ${SCREENSHOTS_DIR}/api-framework/solution && python3 -c \"
from router import Router
router = Router()
@router.get('/users/:id')
def get_user(req, id):
    return {'id': int(id), 'name': 'Test User'}
match, params = router.match('GET', '/users/42')
print(f'Route matched: {match}, params: {params}')
print('API Framework: OK')
\"" 2>&1 | head -20

# Task Scheduler - test triggers
run_and_capture "task-scheduler" \
    "cd ${SCREENSHOTS_DIR}/task-scheduler/solution && python3 -c \"
from triggers import IntervalTrigger
from datetime import datetime, timedelta
t = IntervalTrigger(interval=60)
now = datetime.now()
next_time = t.next_run(now)
print(f'Interval 60s, last_run={now}, next={next_time}')
print('Task Scheduler: OK')
\"" 2>&1 | head -10

# Pixel Editor - test canvas
run_and_capture "pixel-editor" \
    "cd ${SCREENSHOTS_DIR}/pixel-editor/solution && python3 -c \"
from canvas import PixelGrid
grid = PixelGrid(16, 16)
grid.set_pixel(0, 0, '#ff0000')
grid.set_pixel(15, 15, '#0000ff')
print(f'Grid size: {grid.width}x{grid.height}')
print(f'Pixel (0,0): {grid.get_pixel(0,0)}')
print(f'Pixel (15,15): {grid.get_pixel(15,15)}')
print('Pixel Editor: OK')
\"" 2>&1 | head -15

# Markdown Blog - test parser
run_and_capture "markdown-blog" \
    "cd ${SCREENSHOTS_DIR}/markdown-blog/solution && python3 -c \"
from parser import parse
html = parse('# Hello World\n\nThis is **bold** text.')
print(f'Input: # Hello World...')
print(f'Output: {html[:100]}...')
print('Markdown Blog: OK')
\"" 2>&1 | head -15

echo ""
echo "=== All screenshots generated ==="
