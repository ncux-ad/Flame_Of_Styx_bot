#!/bin/bash
# =============================================================================
# ФУНКЦИИ РАБОТЫ С TELEGRAM API
# =============================================================================

# Функция получения информации о группе комментариев канала
get_channel_comment_group() {
    local channel_link="$1"
    local bot_token="$2"
    
    if [ -z "$channel_link" ] || [ -z "$bot_token" ]; then
        error "Не указаны channel_link или bot_token"
        return 1
    fi
    
    # Очищаем ссылку от лишних символов
    local clean_link=$(echo "$channel_link" | sed 's/^@//' | sed 's/^https:\/\/t\.me\///' | sed 's/^t\.me\///')
    
    log "Получение информации о канале: $clean_link"
    
    # Получаем информацию о канале
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChat?chat_id=@${clean_link}")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при запросе к Telegram API"
        return 1
    fi
    
    # Проверяем, что запрос успешен
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка в ответе Telegram API: $response"
        return 1
    fi
    
    # Извлекаем ID канала
    local channel_id=$(echo "$response" | grep -o '"id":[^,]*' | head -1 | grep -o '[0-9-]*')
    
    if [ -z "$channel_id" ]; then
        error "Не удалось получить ID канала"
        return 1
    fi
    
    log "ID канала: $channel_id"
    
    # Получаем информацию о связанной группе комментариев
    local chat_response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChat?chat_id=${channel_id}")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при получении информации о чате"
        return 1
    fi
    
    # Извлекаем ID связанной группы
    local linked_chat_id=$(echo "$chat_response" | grep -o '"linked_chat_id":[^,]*' | head -1 | grep -o '[0-9-]*')
    
    if [ -z "$linked_chat_id" ]; then
        warning "У канала нет связанной группы комментариев"
        echo "$channel_id"
        return 0
    fi
    
    log "ID связанной группы комментариев: $linked_chat_id"
    echo "$channel_id,$linked_chat_id"
}

# Функция обработки каналов
process_channels() {
    if [ -z "$CHANNEL_LINKS" ]; then
        info "Ссылки на каналы не указаны"
        return 0
    fi
    
    info "Обработка каналов..."
    
    local native_channels=""
    IFS=',' read -ra CHANNELS <<< "$CHANNEL_LINKS"
    
    for channel in "${CHANNELS[@]}"; do
        channel=$(echo "$channel" | xargs) # Убираем пробелы
        if [ -n "$channel" ]; then
            log "Обработка канала: $channel"
            
            local channel_info
            channel_info=$(get_channel_comment_group "$channel" "$BOT_TOKEN" 2>/dev/null)
            
            if [ $? -eq 0 ] && [ -n "$channel_info" ]; then
                local channel_id=$(echo "$channel_info" | cut -d',' -f1)
                local linked_chat_id=$(echo "$channel_info" | cut -d',' -f2)
                
                if [ -n "$channel_id" ]; then
                    if [ -z "$native_channels" ]; then
                        native_channels="$channel_id"
                    else
                        native_channels="$native_channels,$channel_id"
                    fi
                    
                    if [ -n "$linked_chat_id" ]; then
                        if [ -z "$native_channels" ]; then
                            native_channels="$linked_chat_id"
                        else
                            native_channels="$native_channels,$linked_chat_id"
                        fi
                    fi
                    
                    success "Канал обработан: $channel -> $channel_id"
                else
                    warning "Не удалось получить ID для канала: $channel"
                fi
            else
                warning "Ошибка при обработке канала: $channel"
            fi
        fi
    done
    
    if [ -n "$native_channels" ]; then
        NATIVE_CHANNEL_IDS="$native_channels"
        success "Нативные каналы: $NATIVE_CHANNEL_IDS"
    else
        warning "Не удалось обработать ни одного канала"
    fi
}

# Функция проверки токена бота
validate_bot_token() {
    local token="$1"
    
    if [ -z "$token" ]; then
        error "Токен бота не указан"
        return 1
    fi
    
    if ! is_valid_bot_token "$token"; then
        error "Неверный формат токена бота"
        return 1
    fi
    
    # Проверяем токен через API
    local response=$(curl -s "https://api.telegram.org/bot${token}/getMe")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при проверке токена через API"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Токен бота недействителен: $response"
        return 1
    fi
    
    local bot_username=$(echo "$response" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    success "Токен бота действителен. Username: @$bot_username"
    
    return 0
}

# Функция отправки тестового сообщения
send_test_message() {
    local chat_id="$1"
    local message="$2"
    local bot_token="$3"
    
    if [ -z "$chat_id" ] || [ -z "$message" ] || [ -z "$bot_token" ]; then
        error "Не указаны chat_id, message или bot_token"
        return 1
    fi
    
    local response=$(curl -s -X POST "https://api.telegram.org/bot${bot_token}/sendMessage" \
        -d "chat_id=${chat_id}" \
        -d "text=${message}" \
        -d "parse_mode=HTML")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при отправке сообщения"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка при отправке сообщения: $response"
        return 1
    fi
    
    success "Тестовое сообщение отправлено в чат $chat_id"
    return 0
}

# Функция получения информации о боте
get_bot_info() {
    local bot_token="$1"
    
    if [ -z "$bot_token" ]; then
        error "Токен бота не указан"
        return 1
    fi
    
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getMe")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при получении информации о боте"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка в ответе API: $response"
        return 1
    fi
    
    echo "$response"
    return 0
}

# Функция проверки прав бота в чате
check_bot_permissions() {
    local chat_id="$1"
    local bot_token="$2"
    
    if [ -z "$chat_id" ] || [ -z "$bot_token" ]; then
        error "Не указаны chat_id или bot_token"
        return 1
    fi
    
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChatMember?chat_id=${chat_id}&user_id=${bot_token%%:*}")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при проверке прав бота"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка при проверке прав: $response"
        return 1
    fi
    
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    case "$status" in
        "administrator")
            success "Бот является администратором в чате $chat_id"
            return 0
            ;;
        "member")
            warning "Бот является участником в чате $chat_id (не админ)"
            return 1
            ;;
        "left")
            error "Бот не добавлен в чат $chat_id"
            return 1
            ;;
        "kicked")
            error "Бот заблокирован в чате $chat_id"
            return 1
            ;;
        *)
            warning "Неизвестный статус бота в чате $chat_id: $status"
            return 1
            ;;
    esac
}

# Функция получения списка администраторов чата
get_chat_administrators() {
    local chat_id="$1"
    local bot_token="$2"
    
    if [ -z "$chat_id" ] || [ -z "$bot_token" ]; then
        error "Не указаны chat_id или bot_token"
        return 1
    fi
    
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChatAdministrators?chat_id=${chat_id}")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при получении списка администраторов"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка в ответе API: $response"
        return 1
    fi
    
    echo "$response"
    return 0
}

# Функция создания webhook
set_webhook() {
    local webhook_url="$1"
    local bot_token="$2"
    
    if [ -z "$webhook_url" ] || [ -z "$bot_token" ]; then
        error "Не указаны webhook_url или bot_token"
        return 1
    fi
    
    local response=$(curl -s -X POST "https://api.telegram.org/bot${bot_token}/setWebhook" \
        -d "url=${webhook_url}")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при установке webhook"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка при установке webhook: $response"
        return 1
    fi
    
    success "Webhook установлен: $webhook_url"
    return 0
}

# Функция удаления webhook
delete_webhook() {
    local bot_token="$1"
    
    if [ -z "$bot_token" ]; then
        error "Токен бота не указан"
        return 1
    fi
    
    local response=$(curl -s -X POST "https://api.telegram.org/bot${bot_token}/deleteWebhook")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при удалении webhook"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка при удалении webhook: $response"
        return 1
    fi
    
    success "Webhook удален"
    return 0
}

# Функция получения информации о webhook
get_webhook_info() {
    local bot_token="$1"
    
    if [ -z "$bot_token" ]; then
        error "Токен бота не указан"
        return 1
    fi
    
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getWebhookInfo")
    
    if [ $? -ne 0 ]; then
        error "Ошибка при получении информации о webhook"
        return 1
    fi
    
    local ok=$(echo "$response" | grep -o '"ok":true' || echo "")
    if [ -z "$ok" ]; then
        error "Ошибка в ответе API: $response"
        return 1
    fi
    
    echo "$response"
    return 0
}
