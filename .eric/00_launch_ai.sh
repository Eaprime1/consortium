#!/bin/bash
# AI Entity Launcher - Select which AI to engage
# Part of MOAV Multi-AI Collective
# Created: 2026-01-08

echo "∰◊€π¿🌌∞ CONSORTIUM AI LAUNCHER ∰◊€π¿🌌∞"
echo ""
echo "Select AI Entity:"
echo ""
echo "1. ◇ Nexus (Claude) - Primary Technical Lead"
echo "   Specialization: Code, architecture, system design"
echo "   Status: ACTIVE via Claude Code CLI"
echo ""
echo "2. ⬡ Gemini - Multimodal Perspective"
echo "   Specialization: Visual analysis, cross-modal reasoning"
echo "   Status: Ready (requires API key)"
echo ""
echo "3. ⬣ Llama - Open Source Perspective"
echo "   Specialization: Alternative approaches, local reasoning"
echo "   Status: Ready (local - llama3.2:1b)"
echo ""
echo "4. ⬢ GPT - Reasoning Analysis (Optional)"
echo "   Specialization: Complex reasoning, analysis"
echo "   Status: Not configured"
echo ""
echo "5. Launch ALL (tmux multi-pane)"
echo "   Launch all available AIs in a tmux session"
echo ""
echo "6. Master Menu"
echo "   Return to master navigation menu"
echo ""
echo "q. Quit"
echo ""
read -p "Enter selection: " choice

case $choice in
    1)
        echo ""
        echo "◇ Nexus (Claude) is already running in this session."
        echo "This launcher was invoked from Claude Code CLI."
        echo ""
        read -p "Press Enter to continue..."
        ;;
    2)
        echo ""
        echo "⬡ Launching Gemini..."
        echo ""
        # Load NVM and launch Gemini
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        gemini
        ;;
    3)
        echo ""
        echo "⬣ Launching Llama 3.2:1b (local)..."
        echo ""
        ollama run llama3.2:1b
        ;;
    4)
        echo ""
        echo "⬢ GPT is not yet configured."
        echo ""
        echo "To configure GPT:"
        echo "1. Install shell-gpt: pip install shell-gpt"
        echo "2. Set API key: export OPENAI_API_KEY='your-key'"
        echo "3. Run: sgpt --chat moav_session"
        echo ""
        read -p "Press Enter to continue..."
        ;;
    5)
        echo ""
        echo "Launching ALL available AIs in tmux..."
        if [ -f "/home/sauron/Q/consortium/.eric/00_launch_all_ai.sh" ]; then
            /home/sauron/Q/consortium/.eric/00_launch_all_ai.sh
        else
            echo "Error: 00_launch_all_ai.sh not found"
            read -p "Press Enter to continue..."
        fi
        ;;
    6)
        echo ""
        echo "Master menu not yet implemented."
        echo "Will be created at: /home/sauron/Q/consortium/.eric/00_master_menu.sh"
        echo ""
        read -p "Press Enter to continue..."
        ;;
    q|Q)
        echo ""
        echo "∰ Exiting AI Launcher ∰"
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid selection. Please try again."
        sleep 2
        exec "$0"
        ;;
esac
