# Install and configure Git Secrets for Flame_Of_Styx_bot (Windows)

Write-Host "🔐 Installing Git Secrets..." -ForegroundColor Green

# Check if git-secrets is already installed
try {
    $version = git-secrets --version 2>$null
    if ($version) {
        Write-Host "✅ Git Secrets already installed: $version" -ForegroundColor Green
    }
} catch {
    Write-Host "📦 Git Secrets not found. Installing..." -ForegroundColor Yellow
    
    # Check if we're in WSL
    if ($env:WSL_DISTRO_NAME) {
        Write-Host "🐧 Running in WSL. Installing via apt..." -ForegroundColor Blue
        sudo apt-get update
        sudo apt-get install -y git-secrets
    } else {
        Write-Host "❌ Git Secrets not available on Windows directly." -ForegroundColor Red
        Write-Host "Please install Git Secrets using one of these methods:" -ForegroundColor Yellow
        Write-Host "1. Use WSL (Windows Subsystem for Linux)" -ForegroundColor Yellow
        Write-Host "2. Use Git Bash with git-secrets installed" -ForegroundColor Yellow
        Write-Host "3. Install via Chocolatey: choco install git-secrets" -ForegroundColor Yellow
        Write-Host "4. Download from: https://github.com/awslabs/git-secrets" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "🔧 Configuring Git Secrets for this repository..." -ForegroundColor Blue

# Initialize git-secrets for this repository
git secrets --install

# Add patterns from .gitsecrets file
if (Test-Path ".gitsecrets") {
    Write-Host "📝 Adding patterns from .gitsecrets..." -ForegroundColor Blue
    Get-Content ".gitsecrets" | ForEach-Object {
        $line = $_.Trim()
        # Skip comments and empty lines
        if ($line -and !$line.StartsWith("#")) {
            git secrets --add $line
        }
    }
}

# Add some common patterns
Write-Host "🔍 Adding common secret patterns..." -ForegroundColor Blue
git secrets --add 'password\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'secret\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'token\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'
git secrets --add 'key\s*=\s*[A-Za-z0-9!@#$%^&*()_+-=]{8,}'

# Configure allowed patterns for test files
Write-Host "✅ Configuring allowed patterns for test files..." -ForegroundColor Blue
git secrets --add --allowed 'test_token_[A-Za-z0-9_]+'
git secrets --add --allowed 'test_[A-Za-z0-9_]+'
git secrets --add --allowed 'dummy_[A-Za-z0-9_]+'
git secrets --add --allowed 'example_[A-Za-z0-9_]+'
git secrets --add --allowed 'your_[A-Za-z0-9_]+'

# Configure allowed patterns for documentation
Write-Host "📚 Configuring allowed patterns for documentation..." -ForegroundColor Blue
git secrets --add --allowed 'BOT_TOKEN=test_token_'
git secrets --add --allowed 'ADMIN_IDS=123456789'
git secrets --add --allowed 'DB_PATH=test.db'

# Test the configuration
Write-Host "🧪 Testing Git Secrets configuration..." -ForegroundColor Blue
try {
    git secrets --scan .gitsecrets
    Write-Host "✅ Git Secrets configuration test passed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git Secrets configuration test failed" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Git Secrets successfully installed and configured!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Run 'git secrets --scan' to check existing files" -ForegroundColor White
Write-Host "2. Run 'git secrets --scan-history' to check commit history" -ForegroundColor White
Write-Host "3. Add 'git secrets --scan' to your pre-commit hooks" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To scan specific files:" -ForegroundColor Yellow
Write-Host "   git secrets --scan <file>" -ForegroundColor White
Write-Host ""
Write-Host "📖 For more information:" -ForegroundColor Yellow
Write-Host "   git secrets --help" -ForegroundColor White
