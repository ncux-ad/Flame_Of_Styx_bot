# Cursor CLI Helper Script for Windows
# Этот скрипт предоставляет удобные команды для работы с Cursor CLI

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

function Show-Help {
    Write-Host "🤖 Cursor CLI Helper для Flame of Styx Bot" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Использование:" -ForegroundColor Yellow
    Write-Host "  .\cursor-cli.ps1 [команда] [аргументы]"
    Write-Host ""
    Write-Host "Доступные команды:" -ForegroundColor Yellow
    Write-Host "  help                    - Показать эту справку"
    Write-Host "  version                 - Показать версию Cursor CLI"
    Write-Host "  status                  - Проверить статус аутентификации"
    Write-Host "  login                   - Войти в Cursor"
    Write-Host "  logout                  - Выйти из Cursor"
    Write-Host "  agent [prompt]          - Запустить Cursor Agent"
    Write-Host "  chat                    - Создать новый чат"
    Write-Host "  resume [chatId]         - Продолжить чат"
    Write-Host "  update                  - Обновить Cursor CLI"
    Write-Host "  analyze [файл]          - Анализировать файл проекта"
    Write-Host "  review                  - Провести code review"
    Write-Host "  fix [описание]          - Исправить проблемы в коде"
    Write-Host ""
    Write-Host "Примеры:" -ForegroundColor Green
    Write-Host "  .\cursor-cli.ps1 agent 'Помоги мне исправить баги в проекте'"
    Write-Host "  .\cursor-cli.ps1 analyze app/handlers/admin.py"
    Write-Host "  .\cursor-cli.ps1 review"
    Write-Host "  .\cursor-cli.ps1 fix 'Исправить ошибки типизации'"
}

function Invoke-CursorCommand {
    param([string]$Cmd, [string[]]$Args = @())
    
    $fullCommand = "wsl -d Ubuntu -e bash -c `"~/.local/bin/cursor-agent $Cmd $($Args -join ' ')`""
    Write-Host "Выполняю: $fullCommand" -ForegroundColor Gray
    Invoke-Expression $fullCommand
}

switch ($Command.ToLower()) {
    "help" { Show-Help }
    "version" { Invoke-CursorCommand "--version" }
    "status" { Invoke-CursorCommand "status" }
    "login" { Invoke-CursorCommand "login" }
    "logout" { Invoke-CursorCommand "logout" }
    "agent" { 
        if ($Arguments.Count -gt 0) {
            $prompt = $Arguments -join " "
            Invoke-CursorCommand "agent" @($prompt)
        } else {
            Invoke-CursorCommand "agent"
        }
    }
    "chat" { Invoke-CursorCommand "create-chat" }
    "resume" { 
        if ($Arguments.Count -gt 0) {
            Invoke-CursorCommand "resume" @($Arguments[0])
        } else {
            Invoke-CursorCommand "resume"
        }
    }
    "update" { Invoke-CursorCommand "update" }
    "analyze" {
        if ($Arguments.Count -gt 0) {
            $file = $Arguments[0]
            $prompt = "Проанализируй файл $file в контексте проекта Flame of Styx Bot. Обрати внимание на архитектуру, качество кода, потенциальные проблемы и предложи улучшения."
            Invoke-CursorCommand "agent" @($prompt)
        } else {
            Write-Host "Укажите файл для анализа: .\cursor-cli.ps1 analyze app/handlers/admin.py" -ForegroundColor Red
        }
    }
    "review" {
        $prompt = "Проведи code review проекта Flame of Styx Bot. Проанализируй архитектуру, качество кода, безопасность, производительность и предложи улучшения. Обрати особое внимание на файлы в папке app/."
        Invoke-CursorCommand "agent" @($prompt)
    }
    "fix" {
        if ($Arguments.Count -gt 0) {
            $description = $Arguments -join " "
            $prompt = "Помоги исправить проблемы в проекте Flame of Styx Bot: $description. Проанализируй код, найди проблемы и предложи конкретные исправления."
            Invoke-CursorCommand "agent" @($prompt)
        } else {
            Write-Host "Опишите проблему: .\cursor-cli.ps1 fix 'Исправить ошибки типизации'" -ForegroundColor Red
        }
    }
    default {
        Write-Host "Неизвестная команда: $Command" -ForegroundColor Red
        Write-Host "Используйте '.\cursor-cli.ps1 help' для просмотра доступных команд" -ForegroundColor Yellow
    }
}
