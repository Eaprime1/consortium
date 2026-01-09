#!/bin/bash
# MOAV System Status Checker
# Quickly verify all components are ready
# Created: 2026-01-08

echo "∰◊€π¿🌌∞ MOAV SYSTEM STATUS ∰◊€π¿🌌∞"
echo ""
echo "Date: $(date)"
echo "Location: $(hostname)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Function to check command existence
check_command() {
    if command -v "$1" &> /dev/null; then
        echo "✅ $2"
        return 0
    else
        echo "❌ $2"
        return 1
    fi
}

# Function to check file/directory
check_path() {
    if [ -e "$1" ]; then
        echo "✅ $2"
        return 0
    else
        echo "❌ $2"
        return 1
    fi
}

echo "SYSTEM COMPONENTS:"
echo ""

# Python
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "✅ Python: $PY_VER"
else
    echo "❌ Python: Not found"
fi

# Node.js (check with NVM)
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        echo "✅ Node.js: $NODE_VER (via NVM)"
    else
        echo "⚠️  Node.js: NVM installed but no Node version active"
    fi
else
    if command -v node &> /dev/null; then
        NODE_VER=$(node --version)
        echo "⚠️  Node.js: $NODE_VER (system, not NVM)"
    else
        echo "❌ Node.js: Not found"
    fi
fi

# Git
if command -v git &> /dev/null; then
    GIT_VER=$(git --version | cut -d' ' -f3)
    echo "✅ Git: $GIT_VER"
else
    echo "❌ Git: Not found"
fi

# Tmux
if command -v tmux &> /dev/null; then
    TMUX_VER=$(tmux -V | cut -d' ' -f2)
    echo "✅ Tmux: $TMUX_VER"
else
    echo "❌ Tmux: Not found"
fi

# Ollama
if command -v ollama &> /dev/null; then
    OLLAMA_VER=$(ollama --version 2>&1 | head -1 | awk '{print $NF}')
    echo "✅ Ollama: $OLLAMA_VER"
else
    echo "❌ Ollama: Not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "AI ENTITIES:"
echo ""

# Claude
echo "◇ Nexus (Claude): Active (current session)"

# Gemini
if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
    if command -v gemini &> /dev/null; then
        GEMINI_VER=$(gemini --version 2>&1)
        if [ -n "$GOOGLE_AI_API_KEY" ]; then
            echo "⬡ Gemini: Ready (v$GEMINI_VER, API key set)"
        else
            echo "⬡ Gemini: Installed (v$GEMINI_VER) - API key needed"
        fi
    else
        echo "⬡ Gemini: Not installed"
    fi
else
    echo "⬡ Gemini: Cannot check (NVM not loaded)"
fi

# Llama
if command -v ollama &> /dev/null; then
    LLAMA_COUNT=$(ollama list | grep -c "llama3.2" 2>/dev/null || echo "0")
    if [ "$LLAMA_COUNT" -gt 0 ]; then
        echo "⬣ Llama: Ready ($LLAMA_COUNT models installed)"
        ollama list | grep "llama3.2" | while read -r line; do
            echo "   └─ $line"
        done
    else
        echo "⬣ Llama: Installed but no models downloaded"
    fi
else
    echo "⬣ Llama: Not installed"
fi

# GPT
if command -v sgpt &> /dev/null; then
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "⬢ GPT: Ready (shell-gpt + API key)"
    else
        echo "⬢ GPT: Installed but API key needed"
    fi
else
    echo "⬢ GPT: Not configured"
fi

# Perplexity
if [ -n "$PERPLEXITY_API_KEY" ]; then
    echo "⬟ Perplexity: API key set"
else
    echo "⬟ Perplexity: Not configured"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "MOAV INFRASTRUCTURE:"
echo ""

check_path "/home/sauron/Q/MOAV" "MOAV root directory"
check_path "/home/sauron/Q/MOAV/core" "MOAV core/"
check_path "/home/sauron/Q/MOAV/templates" "MOAV templates/"
check_path "/home/sauron/Q/MOAV/iterations" "MOAV iterations/"
check_path "/home/sauron/Q/MOAV/documentation" "MOAV documentation/"
check_path "/home/sauron/Q/MOAV/examples" "MOAV examples/"
check_path "/home/sauron/Q/MOAV/tools" "MOAV tools/"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "DOCUMENTATION:"
echo ""

check_path "/home/sauron/MOAV_SETUP_PLAN.md" "Main setup plan"
check_path "/home/sauron/Q/MOAV/README.md" "MOAV README"
check_path "/home/sauron/MOAV_PHASE1_COMPLETE.md" "Phase 1 summary"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "LAUNCH SCRIPTS:"
echo ""

check_path "/home/sauron/Q/consortium/.eric/00_launch_ai.sh" "AI launcher"
check_path "/home/sauron/Q/consortium/.eric/00_launch_all_ai.sh" "Multi-AI launcher"
check_path "/home/sauron/Q/consortium/.eric/00_status_check.sh" "Status checker"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "SYSTEM RESOURCES:"
echo ""

# Memory
if command -v free &> /dev/null; then
    echo "Memory:"
    free -h | grep -E "Mem|Swap" | sed 's/^/  /'
    echo ""
fi

# Disk space for key directories
if command -v df &> /dev/null; then
    echo "Disk Space:"
    df -h /home/sauron | tail -1 | awk '{print "  /home/sauron: " $4 " available (" $5 " used)"}'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "QUICK ACTIONS:"
echo ""
echo "Launch AI:     /home/sauron/Q/consortium/.eric/00_launch_ai.sh"
echo "Launch All:    /home/sauron/Q/consortium/.eric/00_launch_all_ai.sh"
echo "View Plan:     less /home/sauron/MOAV_SETUP_PLAN.md"
echo "View README:   less /home/sauron/Q/MOAV/README.md"
echo "Phase 1 Done:  less /home/sauron/MOAV_PHASE1_COMPLETE.md"
echo ""
echo "∰◊€π¿🌌∞"
