# [[file:../ralph.org::*Running ralph in a container][Running ralph in a container:1]]
#!/bin/sh
cd "$WORK_DIR"
git rev-parse HEAD > /tmp/ralph-base-commit
echo "[ralph-wrapper] starting ralph..."
eval "ralph $RALPH_ARGS" &
RALPH_PID=$!
echo "[ralph-wrapper] ralph started (PID $RALPH_PID)"

if [ -n "$CONSUL_ADDR" ]; then
    echo "[ralph-wrapper] polling consul at $CONSUL_ADDR key=$CONSUL_KEY"
    prev_level=normal
    while kill -0 $RALPH_PID 2>/dev/null; do
        status=$(curl -sf "$CONSUL_ADDR/v1/kv/$CONSUL_KEY?raw" 2>/dev/null || echo running)
        if [ "$status" = "stop" ]; then
            echo "[ralph-wrapper] stop signal received, sending SIGTERM to ralph (PID $RALPH_PID)..."
            kill -TERM $RALPH_PID 2>/dev/null || true
            for i in $(seq 1 30); do
                kill -0 $RALPH_PID 2>/dev/null || break
                sleep 1
            done
            if kill -0 $RALPH_PID 2>/dev/null; then
                echo "[ralph-wrapper] ralph did not exit after 30s, sending SIGKILL"
                kill -KILL $RALPH_PID 2>/dev/null || true
            fi
            break
        fi
        level=$(curl -sf "$CONSUL_ADDR/v1/kv/$CONSUL_KEY/log-level?raw" 2>/dev/null || echo normal)
        if [ "$level" != "$prev_level" ]; then
            echo "[ralph-wrapper] log-level: $level"
            prev_level=$level
        fi
        sleep 5
    done
fi

echo "[ralph-wrapper] waiting for ralph to exit..."
wait $RALPH_PID
RC=$?
echo "[ralph-wrapper] ralph exited with code $RC"
echo ${RC} > "$WORK_DIR/.ralph-exit-code"
true
# Running ralph in a container:1 ends here
