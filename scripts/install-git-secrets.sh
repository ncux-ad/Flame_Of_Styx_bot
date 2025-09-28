#!/bin/bash
# Install and configure Git Secrets for Flame_Of_Styx_bot

set -e

echo "🔐 Installing Git Secrets..."

# Check if git-secrets is already installed
if command -v git-secrets &> /dev/null; then
    echo "✅ Git Secrets already installed"
    git-secrets --version
else
    echo "📦 Installing Git Secrets..."
    
    # For Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y git-secrets
    # For macOS
    elif command -v brew &> /dev/null; then
        brew install git-secrets
    # For CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y git-secrets
    # For Fedora
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y git-secrets
    else
        echo "❌ Package manager not found. Please install git-secrets manually."
        echo "   Visit: https://github.com/awslabs/git-secrets"
        exit 1
    fi
fi

echo "🔧 Configuring Git Secrets for this repository..."

# Initialize git-secrets for this repository
git secrets --install

# Add patterns from .gitsecrets file
if [ -f ".gitsecrets" ]; then
    echo "📝 Adding patterns from .gitsecrets..."
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ ! "$line" =~ ^#.*$ ]] && [[ -n "$line" ]]; then
            git secrets --add "$line"
        fi
    done < .gitsecrets
fi

# Add some common patterns
echo "🔍 Adding common secret patterns..."
git secrets --add 'password\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'secret\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'token\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'key\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'

# Configure allowed patterns for test files
echo "✅ Configuring allowed patterns for test files..."
git secrets --add --allowed 'test_token_[A-Za-z0-9_]+'
git secrets --add --allowed 'test_[A-Za-z0-9_]+'
git secrets --add --allowed 'dummy_[A-Za-z0-9_]+'
git secrets --add --allowed 'example_[A-Za-z0-9_]+'
git secrets --add --allowed 'your_[A-Za-z0-9_]+'

# Configure allowed patterns for documentation
echo "📚 Configuring allowed patterns for documentation..."
git secrets --add --allowed 'BOT_TOKEN=test_token_'
git secrets --add --allowed 'ADMIN_IDS=123456789'
git secrets --add --allowed 'DB_PATH=test.db'

# Test the configuration
echo "🧪 Testing Git Secrets configuration..."
if git secrets --scan .gitsecrets; then
    echo "✅ Git Secrets configuration test passed"
else
    echo "❌ Git Secrets configuration test failed"
    exit 1
fi

echo "🎉 Git Secrets successfully installed and configured!"
echo ""
echo "📋 Next steps:"
echo "1. Run 'git secrets --scan' to check existing files"
echo "2. Run 'git secrets --scan-history' to check commit history"
echo "3. Add 'git secrets --scan' to your pre-commit hooks"
echo ""
echo "🔍 To scan specific files:"
echo "   git secrets --scan <file>"
echo ""
echo "📖 For more information:"
echo "   git secrets --help"
