# AI API Gateway

Прокси-сервер к OpenRouter с авторизацией по API-ключу из Redis и жёстким ограничением **5 запросов в минуту на пользователя**.

Структура приложения:

- `app/main.py` — точка входа и инициализация FastAPI, Redis и HTTP-клиента;
- `app/routes.py` — HTTP-эндпоинты и HTTP-ошибки;
- `app/dependencies.py` — FastAPI-зависимость авторизации по Bearer API-ключу;
- `app/settings.py` — Pydantic `Settings`, который читает `.env` и переменные окружения;
- `app/services/gateway.py` — бизнес-правила, включая лимит `REQUESTS_PER_MINUTE = 5`;
- `app/services/infrastructure.py` — обращения к Redis и OpenRouter.

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

Перед запуском укажите ключ OpenRouter в `.env`:

```dotenv
OPENROUTER_API_KEY=your-openrouter-key
```

Добавьте API-ключ пользователя:

```bash
docker compose exec redis redis-cli SET api_key:demo-key demo-user
```

## Ручки

### `GET /health`

Проверка доступности сервиса.

### `POST /v1/chat/completions`

Проксирует запрос в OpenRouter. Требуется заголовок `Authorization: Bearer <API key>`.

```bash
curl http://localhost:8000/v1/chat/completions \
  -H 'Authorization: Bearer demo-key' \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

Если не передать `model`, шлюз использует `openrouter/free`: OpenRouter сам выберет доступную бесплатную модель. Можно передать любой поддерживаемый OpenRouter идентификатор модели в поле `model`.

Шестой запрос пользователя за 60 секунд вернёт `429 Too Many Requests` и заголовок `Retry-After`.
