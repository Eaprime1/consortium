#!/bin/bash
# Multi-AI Tmux Launcher - Launch all AIs in split panes
# Part of MOAV Multi-AI Collective
# Created: 2026-01-08

SESSION_NAME="moav_collective"

echo "∰◊€π¿🌌∞ MULTI-AI COLLECTIVE LAUNCHER ∰◊€π¿🌌∞"
echo ""
echo "This will launch all available AI entities in a tmux session."
echo "Each AI will have its own pane in the terminal."
echo ""
echo "Available AIs:"
echo "  ⬡ Gemini (requires API key)"
echo "  ⬣ Llama 3.2:1b (local)"
echo ""
echo "Note: ◇ Nexus (Claude) is already running in your current session."
echo ""
read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo ""
    echo "Session '$SESSION_NAME' already exists."
    read -p "Attach to existing session? (y/n): " attach
    if [ "$attach" = "y" ] || [ "$attach" = "Y" ]; then
        tmux attach-session -t "$SESSION_NAME"
    fi
    exit 0
fi

echo ""
echo "Creating tmux session: $SESSION_NAME"

# Create new session with first pane
tmux new-session -d -s "$SESSION_NAME" -n "AI_Collective"

# Split into 2 vertical panes
tmux split-window -h -t "$SESSION_NAME"

# Split each pane horizontally to get 4 total panes
tmux split-window -v -t "$SESSION_NAME:0.0"
tmux split-window -v -t "$SESSION_NAME:0.2"

# Pane layout:
# 0 (top-left)     | 2 (top-right)
# 1 (bottom-left)  | 3 (bottom-right)

# Pane 0: Status/Info
tmux select-pane -t 0
tmux send-keys "clear" C-m
tmux send-keys "echo '∰◊€π¿🌌∞ MOAV COLLECTIVE - STATUS ∰◊€π¿🌌∞'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "echo 'AI Entities Active:'" C-m
tmux send-keys "echo '  ◇ Nexus (Claude) - Running in main session'" C-m
tmux send-keys "echo '  ⬡ Gemini - Pane 1 (bottom-left)'" C-m
tmux send-keys "echo '  ⬣ Llama - Pane 2 (top-right)'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "echo 'Usage:'" C-m
tmux send-keys "echo '  Ctrl+B then arrow keys - Navigate panes'" C-m
tmux send-keys "echo '  Ctrl+B then d - Detach (keep running)'" C-m
tmux send-keys "echo '  Ctrl+B then [ - Scroll mode (q to exit)'" C-m
tmux send-keys "echo '  Type \"exit\" in AI pane to close it'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "echo 'Session: $SESSION_NAME'" C-m
tmux send-keys "echo 'Created: $(date)'" C-m
tmux send-keys "echo ''" C-m

# Pane 1: Gemini (bottom-left)
tmux select-pane -t 1
tmux send-keys "clear" C-m
tmux send-keys "echo '⬡ Gemini Ready'" C-m
tmux send-keys "echo 'Loading NVM and launching Gemini CLI...'" C-m
tmux send-keys "export NVM_DIR=\"\$HOME/.nvm\"" C-m
tmux send-keys "[ -s \"\$NVM_DIR/nvm.sh\" ] && \\. \"\$NVM_DIR/nvm.sh\"" C-m
tmux send-keys "echo 'Type: gemini (to start)'" C-m
# Don't auto-launch - let user start when ready
# tmux send-keys "gemini" C-m

# Pane 2: Llama (top-right)
tmux select-pane -t 2
tmux send-keys "clear" C-m
tmux send-keys "echo '⬣ Llama 3.2:1b Ready (Local)'" C-m
tmux send-keys "echo 'Type: ollama run llama3.2:1b (to start)'" C-m
# Don't auto-launch - let user start when ready
# tmux send-keys "ollama run llama3.2:1b" C-m

# Pane 3: Reserved (bottom-right)
tmux select-pane -t 3
tmux send-keys "clear" C-m
tmux send-keys "echo 'Reserved for additional AI or monitoring'" C-m
tmux send-keys "echo ''" C-m
tmux send-keys "echo 'Suggestions:'" C-m
tmux send-keys "echo '  - htop (system monitoring)'" C-m
tmux send-keys "echo '  - GPT (if configured)'" C-m
tmux send-keys "echo '  - Perplexity (if configured)'" C-m
tmux send-keys "echo '  - Custom commands'" C-m

# Set pane 0 as active (status pane)
tmux select-pane -t 0

# Attach to the session
echo ""
echo "Attaching to session..."
sleep 1
tmux attach-session -t "$SESSION_NAME"
