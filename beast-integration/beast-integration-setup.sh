#!/bin/bash

# Beast Agent Integration Setup Script for LIBR8
set -e

LIBR8_DIR="$HOME/LIBR8"
INTEGRATION_DIR="$LIBR8_DIR/beast-integration"

echo "Setting up Beast Agent Integration in LIBR8..."

# Create integration directory structure
mkdir -p "$INTEGRATION_DIR"/{agent-patterns,role-system,state-machine,memory,execution,unified}

cd "$INTEGRATION_DIR"

echo "Pulling AutoGen agent patterns..."
mkdir -p temp-autogen
git clone --depth 1 --filter=blob:none --sparse https://github.com/microsoft/autogen.git temp-autogen
cd temp-autogen
git sparse-checkout set autogen/agentchat autogen/coding
cp -r autogen/agentchat ../agent-patterns/
cp -r autogen/coding ../agent-patterns/
cd ..
rm -rf temp-autogen

echo "Pulling CrewAI role system..."
mkdir -p temp-crewai
git clone --depth 1 --filter=blob:none --sparse https://github.com/crewAIInc/crewAI.git temp-crewai
cd temp-crewai
git sparse-checkout set src/crewai/agent src/crewai/task src/crewai/crew.py
cp -r src/crewai/* ../role-system/
cd ..
rm -rf temp-crewai

echo "Pulling LangGraph state machine..."
mkdir -p temp-langgraph
git clone --depth 1 --filter=blob:none --sparse https://github.com/langchain-ai/langgraph.git temp-langgraph
cd temp-langgraph
git sparse-checkout set langgraph
cp -r langgraph ../state-machine/
cd ..
rm -rf temp-langgraph

echo "Pulling Chroma memory components..."
mkdir -p temp-chroma
git clone --depth 1 --filter=blob:none --sparse https://github.com/chroma-core/chroma.git temp-chroma
cd temp-chroma
git sparse-checkout set chromadb
cp -r chromadb ../memory/
cd ..
rm -rf temp-chroma

echo "Pulling OpenInterpreter execution engine..."
mkdir -p temp-interpreter
git clone --depth 1 --filter=blob:none --sparse https://github.com/OpenInterpreter/open-interpreter.git temp-interpreter
cd temp-interpreter
git sparse-checkout set interpreter/core
mkdir -p ../execution/interpreter
cp -r interpreter/core/* ../execution/interpreter/
cd ..
rm -rf temp-interpreter

echo "Pulling Playwright browser automation..."
mkdir -p temp-playwright
git clone --depth 1 --filter=blob:none --sparse https://github.com/microsoft/playwright.git temp-playwright
cd temp-playwright
git sparse-checkout set packages/playwright-core/src
mkdir -p ../execution/browser
cp -r packages/playwright-core/src/* ../execution/browser/
cd ..
rm -rf temp-playwright

echo "Creating unified directory structure..."
mkdir -p unified/{agents,memory,tools,workflows,core}

# Create integration map file
cat > unified/INTEGRATION_MAP.md << 'EOF'
# Beast Agent Integration Map

## Source Locations:
- **Agent Patterns**: ../agent-patterns/ (from AutoGen)
- **Role System**: ../role-system/ (from CrewAI) 
- **State Machine**: ../state-machine/ (from LangGraph)
- **Memory**: ../memory/ (from Chroma)
- **Code Execution**: ../execution/interpreter/ (from OpenInterpreter)
- **Browser Automation**: ../execution/browser/ (from Playwright)

## Integration Points:
- Extract conversation patterns from agent-patterns/agentchat/
- Extract role definitions from role-system/agent/
- Extract task delegation from role-system/task/
- Extract state management from state-machine/langgraph/
- Extract vector ops from memory/chromadb/
- Extract code exec from execution/interpreter/
- Extract browser control from execution/browser/
EOF

echo "Beast integration setup complete!"
echo "Location: $INTEGRATION_DIR"
echo "Ready to extract and unify components in unified/ directory"

# Make the script executable
chmod +x "$0"