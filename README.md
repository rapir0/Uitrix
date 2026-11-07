# Uitrix CRM

Self-hosted CRM для команд аутсорс-технической поддержки: канбан-доска со статусами, управление контрагентами и контактами, интеграция с Telegram-ботом для приёма заявок.

Разворачивается на собственном сервере (Debian 12 + Docker), данные не покидают ваш контур.

## Возможности

- **Канбан** по статусам с drag & drop, сортировкой и фильтрами («Мои тикеты», контрагент, период).
- **Контрагенты** с подразделениями и контактами (ФИО, Telegram `@username`, телефон).
- **Telegram-бот**: создание заявок из чата, приём вложений (фото, документы), уведомления клиенту о смене статуса.
- **Роли** admin / agent, аудит всех изменений, принудительная смена пароля при первом входе.
- **Отчёты**: за сегодня и за период по агентам и контрагентам.
- **Статусы и подстатусы** настраиваются в веб-интерфейсе, удаление — soft-delete (тикеты не теряются).

## Стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic
- **БД:** PostgreSQL 16
- **Frontend:** Jinja2 + Bootstrap 5 + htmx + Alpine.js, SortableJS (drag & drop)
- **Бот:** python-telegram-bot (webhook в prod, polling в dev)
- **Инфраструктура:** Docker Compose, Nginx + Let's Encrypt, Debian 12

## Быстрый старт (локально)

Требуется: WSL2 (или Linux), Docker Engine, Git.

```bash
git clone git@github.com:rapir0/Uitrix.git
cd Uitrix

# 1. Создать .env из шаблона и заполнить секреты
cp .env.example .env
# отредактируйте .env: POSTGRES_PASSWORD, ADMIN_INITIAL_PASSWORD, TELEGRAM_BOT_TOKEN

# 2. Поднять стек
docker compose up -d --build

# 3. Проверить
curl http://localhost:8000/health
# → {"status":"ok","env":"dev"}
```

Веб-интерфейс: http://localhost:8000
API-документация (Swagger): http://localhost:8000/docs

**Первый вход:** учётная запись `uitlocal` (или значение `ADMIN_USERNAME` из `.env`), пароль — `ADMIN_INITIAL_PASSWORD` из `.env`. При первом входе потребуется сменить пароль.

## Развёртывание на сервере

Инструкция появится в `docs/deploy.md` по мере готовности инфраструктуры. Целевая конфигурация:

- домен `crm.ghostnode.ru` → Nginx (TLS от Let's Encrypt) → backend-контейнер;
- PostgreSQL — только на `127.0.0.1`, не доступен извне;
- ежедневный `pg_dump` по cron с ротацией 14 дней;
- бэкап вложений через rsync;
- Telegram-бот в режиме webhook.

## Документация

- [Product Vision v1.1 (RU)](docs/product-vision.md) · [EN](docs/product-vision.en.md) — что строим, для кого, scope MVP
- [Architecture](docs/architecture.md) — технический обзор (в работе)

## Разработка

Рабочий процесс:

```bash
git checkout main && git pull
git checkout -b feat/<краткое-имя>
# ... правки ...
git add -A
git commit -m "feat: <что сделано>"
git push -u origin feat/<краткое-имя>
# → открыть Pull Request на GitHub → merge → delete branch
```

Ветка `main` защищена: только через PR.

Соглашение о коммитах — [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.

## Статус

**MVP в активной разработке.** Дорожная карта и scope — раздел 12 в [Product Vision](docs/product-vision.md#12-scope-mvp-и-метрики).

Не входит в MVP: SPA-фронтенд, мобильное приложение, SLA-таймеры, multi-tenancy, интеграции с почтой/WhatsApp/VK.

## Лицензия

TBD (планируется проприетарная лицензия для коммерческого распространения).