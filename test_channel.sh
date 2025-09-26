#!/bin/bash

# Функция определения группы комментариев для канала
get_channel_comment_group() {
    local channel_link="$1"
    local bot_token="$2"
    
    if [ -z "$bot_token" ] || [ -z "$channel_link" ]; then
        return 1
    fi
    
    # Очищаем ссылку от @ и https://
    local channel_username=$(echo "$channel_link" | sed 's|https://t.me/||g' | sed 's|@||g' | sed 's|^t.me/||g')
    
    echo "Определение группы комментариев для канала: $channel_username" >&2
    
    # Получаем информацию о канале через Telegram Bot API
    local response=$(curl -s "https://api.telegram.org/bot${bot_token}/getChat?chat_id=@${channel_username}")
    
    if echo "$response" | grep -q '"ok":true'; then
        # Извлекаем ID канала более безопасно
        local channel_id=$(echo "$response" | grep -o '"id":[^,}]*' | cut -d':' -f2 | tr -d ' "')
        
        if [ -n "$channel_id" ] && [ "$channel_id" != "null" ]; then
            echo "ID канала $channel_username: $channel_id" >&2
            
            # Проверяем, есть ли связанная группа комментариев
            if echo "$response" | grep -q '"linked_chat"'; then
                local linked_chat_id=$(echo "$response" | grep -o '"linked_chat":[^,}]*' | cut -d':' -f2 | tr -d ' "')
                if [ -n "$linked_chat_id" ] && [ "$linked_chat_id" != "null" ]; then
                    echo "Найдена группа комментариев: $linked_chat_id для канала $channel_username" >&2
                    printf "%s" "$linked_chat_id"
                    return 0
                fi
            fi
            
            echo "Группа комментариев не найдена для канала $channel_username, используем ID канала" >&2
            printf "%s" "$channel_id"
            return 0
        else
            echo "Не удалось извлечь ID канала $channel_username" >&2
            return 1
        fi
    else
        echo "Ошибка получения информации о канале $channel_username" >&2
        echo "Ответ API: $response" >&2
        return 1
    fi
}

# Тестируем функцию
echo "Тестируем функцию get_channel_comment_group:"
result=$(get_channel_comment_group "@danilin_psy" "7977609078:AAHdBkjqov_KCHdsRr7QC_dolaa9FNNMw68")
echo "Результат: '$result'"
echo "Длина результата: ${#result}"
