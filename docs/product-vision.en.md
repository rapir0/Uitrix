# Uitrix CRM — Product Vision

> **Version:** 1.1
> **Status:** Draft
> **Date:** 2026-11-07
> **Owner:** rapir0

## 0. Summary

Uitrix CRM is a self-hosted ticket management system for outsourced technical support teams. Its primary interface is a kanban board organized by status, integrated with a Telegram bot through which clients create tickets. The system stores contractors, their departments and contacts, and manages the full ticket lifecycle: from creation to closure, including transfer between agents and audit of all actions.

**Core idea:** support that starts in Telegram (where clients already live) and turns into a structured process in the web interface — without expensive Zendesk/Freshdesk subscriptions and with full data control.

## 1. Problem and Target Audience

**Problem.** Small outsourced support teams (2–20 people) manage tickets in messengers, Excel, and Trello-like boards. This leads to:
- lost tickets and forgotten clients;
- no unified history per contractor;
- no visibility into team workload;
- manual ticket handover and, consequently, delays.

Zendesk, Freshdesk, and Jira Service Management are expensive ($15–50 per agent per month), are not Telegram-first, and do not support self-hosting.

**Target audience.**
- Outsourced support teams in SMB (2–20 agents).
- Their clients (contractors) — companies whose employees contact support via Telegram.
- Roles in the team that buys Uitrix: owner, team lead/admin, agent.

**Not a fit.** Enterprises with hundreds of agents (need multi-tenancy and an SLA engine), teams without Telegram, teams that need telephony and calls.

## 2. Glossary

| Term | Definition |
|---|---|
| **Ticket** | A unit of work: a client request requiring an agent action. |
| **Contractor** | The client company to which its contacts and departments belong. |
| **Department** | A structural unit of a contractor (branch, office). A contact may belong to a department. |
| **Contractor contact** | A person on the client side (full name, Telegram @username, phone). Does not log in to the CRM. The ticket initiator. |
| **CRM user** (user, agent, admin) | A member of the Uitrix-owning team. Logs in to the web interface. Takes tickets into work. |
| **Agent** | A CRM user with the `agent` role. Sees and processes tickets. |
| **Admin** | A CRM user with the `admin` role. Manages users, contractors, statuses. |
| **Status** | A state in the ticket lifecycle (New, In progress, …). Corresponds to a kanban column. |
| **Substatus** | A refinement of a status (e.g., "On hold" → "Waiting for client"). |
| **Attachment** | A file (image, document) attached to a ticket. |

## 3. Tech Stack and Architecture

**High-level diagram:**
```
[Telegram Bot] ←→ [Backend API] ←→ [PostgreSQL]
                       ↑
                  [Nginx + TLS]
                       ↑
                   [Browser]
```

**Stack:**
- **Backend:** Python 3.12 + FastAPI, SQLAlchemy 2 (async), Alembic for migrations.
- **DB:** PostgreSQL 16. Backups — daily `pg_dump` via cron + 14-day rotation + monthly restore verification.
- **Frontend:** server-side rendering with Jinja2 + Bootstrap 5 + htmx + Alpine.js. Kanban drag & drop via SortableJS. No separate SPA build — simpler deployment, less infrastructure.
- **Reverse proxy:** Nginx with TLS (Let's Encrypt). Backend port 8000 is not exposed externally; accessible only through Nginx.
- **Telegram Bot:** python-telegram-bot (v21+), webhook mode in prod, polling locally for development.
- **Attachments:** local directory `/var/uitrix/uploads/` (with future migration to S3/MinIO). Served via the backend with permission checks.
- **Containerization:** Docker + Docker Compose (local and prod). Services: `backend`, `db`, `bot`, `nginx`, `cron` (backups).

## 4. Web Interface

### 4.1. First login

On first launch, an admin user is created from environment variables `ADMIN_USERNAME` (default `uitlocal`) and `ADMIN_INITIAL_PASSWORD` (set in `.env`, **never stored in the repository**).

On first login, the user is required to change the password — until then, only the password-change form and logout are accessible.

### 4.2. "Kanban" tab (main view)

- Columns represent ticket statuses.
- Tickets within a column are sorted by `created_at`, direction toggleable (newest first / oldest first). Preference is stored per user.
- Ticket card — "sticker" style:
  - **Row 1:** contractor name; background is darker than the card body.
  - **Row 2:** initiator — full name or Telegram `@username`.
  - **Body:** ticket text (truncated to 4–5 lines with "…").
  - **Bottom:** created date and time in `DD.MM.YYYY HH:MM` format.
- Drag & drop between columns changes the status. Order within a column is determined by sorting, not by manual repositioning. **In MVP, dragging changes only status, not position.**
- Clicking a card opens a modal:
  - full text, attachments, change history;
  - edit (status, substatus, assignee, contractor, department, text);
  - transfer to another agent;
  - close (move to "Done" / "Not done").
- "+" button — create a ticket manually (see section 7.1).
- Filters above the board: "My tickets" (toggle), "Contractor", "Status" (to hide empty columns), "Period".

### 4.3. "Contractors" tab

List of contractors with search by name and INN. Clicking a row opens the contractor card.

Row action icons:
- ✏️ **Details** — edit fields;
- 🏠 **Departments** — contractor's departments (CRUD);
- 👤 **Contacts** — contractor's contacts with their department.

**Contractor fields:** name, INN, website, general phone, address, list of departments (name + address), "Service contract" flag.

### 4.4. "Employees" tab (contractor contacts)

List of **contractor contacts** — people on the client side who reach out for support. These are not CRM users; they do not log in.

Displayed fields: full name, Telegram `@username`, phone, contractor, department, open ticket count.

Filters:
- by contractor (dropdown);
- by department (dropdown);
- by name / `@username` — text search;
- "Has open tickets" checkbox.

### 4.5. "CRM Users" tab (admin only)

Accessible only to the `admin` role.

List of CRM users: full name, email, Telegram `@username`, role, status (active/blocked), last login date.

Actions: create, edit, deactivate, reset password.

### 4.6. "Settings" tab

**Personal settings (all roles):**
- display full name or Telegram `@username` in the UI;
- show/hide Telegram avatar (best-effort);
- UI language (Russian only for now);
- theme (light / dark / system).

**System settings (admin only):**
- manage statuses and substatuses (see section 5);
- Telegram bot settings (token, mode: polling/webhook, welcome message);
- backup settings.

**Telegram avatars.** Fetched via `getUserProfilePhotos`, only if the user has explicitly interacted with the bot and a photo is available. The API does not guarantee a photo; if unavailable — initials in a circle. Optional feature, not a blocker.

### 4.7. "Reports" tab (admin only)

Minimal set for MVP:
- **Today** — created / closed / transferred / in progress / unassigned;
- **Period** — per-agent summary (tickets taken and closed);
- **By contractor** — top 10 by number of open tickets.

## 5. Statuses and Substatuses

**Seed statuses (created on first launch):**

| Status | Type | Default substatuses |
|---|---|---|
| New | open | — |
| In progress | open | — |
| On hold | open | Deferred by client, Waiting for tech support, Waiting for third party |
| Transferred to colleague | open | — |
| Done | closed | — |
| Not done | closed | Not relevant, Not agreed, No client response |

**Rules:**
- Statuses and substatuses are created and edited in the web UI (admin only).
- Status deletion is a **soft-delete**: `is_archived = true`. The column is hidden from the board but its tickets remain. If the status is non-empty, the admin sees a warning with the ticket count and options: (a) archive together with tickets, (b) move tickets to another status first, (c) cancel.
- Each status has a color (for visual distinction on the board).
- Status attributes: `is_closed` (closing status), `is_default` (for new tickets — "New"), `position` (column order).
- Substatuses are selected after the status in both bot and web.
- Tickets are created/closed/edited/transferred both in bot and in web.

## 6. Telegram Bot

### 6.1. Interaction scenarios

**6.1.1. Creating a ticket via the bot**

1. The client taps "➕ Create" **or** forwards a message from another chat.
2. If via the button — the bot asks for the ticket text. Can be typed or forwarded.
3. If forwarded — the bot records the initiator's `telegram_id` and `@username`/name (best-effort).
4. If the account is hidden or text was typed manually — the bot asks for the client's name and phone (or `@username`).
5. **Contractor binding:**
   - if `telegram_id` is known — the bound contractor and (if set) department are used;
   - if not — the bot asks for a contractor from the list (inline buttons) and department (optional);
   - a new contractor contact is created with this `telegram_id`.
6. The bot asks for the status (default — "New", can be changed immediately).
7. The ticket is created; the client receives confirmation with the ticket number.

**6.1.2. Client notifications**

- When the ticket status changes, the client receives a notification in the same bot chat: "Ticket #123 moved to 'In progress'".
- Notifications can be disabled via `/mute` (per-contact setting).

**6.1.3. Status view**

- `/status` command — list of the client's active tickets with current statuses.

**6.1.4. Attachments**

- When creating a ticket (or later), the client can send photos, documents, voice messages.
- Files are stored at `/var/uitrix/uploads/{ticket_id}/{uuid}.{ext}`.
- Metadata (type, size, name) stored in the DB.
- Single-file limit: 20 MB (Telegram standard). Attachment limit per ticket: 10.

### 6.2. Mode

- **Dev:** polling (long-polling). No public URL required.
- **Prod:** webhook. URL: `https://crm.ghostnode.ru/telegram/webhook/{secret}`. Secret — in `.env`, validated on incoming requests. Served via Nginx with TLS.

### 6.3. Contact binding

Open question: how to avoid duplicates when one person writes from two accounts or forwards someone else's messages. For MVP:
- **One `telegram_id` = one contact.** Duplicates by name/phone are possible.
- In the web UI, an admin can **merge** two contacts into one (all tickets are re-assigned).
- "Possible duplicates" section in the admin panel — post-MVP.

## 7. Processes

### 7.1. Creating a ticket

**Via bot:** see section 6.1.1.

**Via web:** "+" button on the kanban → modal with fields:
- contractor (searchable dropdown) — required;
- department (dropdown, depends on contractor) — optional;
- contact (searchable dropdown by name/username) or create new — required;
- ticket text — required;
- attachments — optional;
- status (default "New") and substatus;
- assignee (default — current user).

### 7.2. Ticket transfer

- From the ticket card or by dragging to the "Transferred to colleague" status.
- Modal: select agent (dropdown of active `agent`/`admin` users), optional comment, "Transfer" button.
- After transfer: `assignee_user_id` changes, status → "Transferred to colleague", the new assignee receives a **Telegram** notification (not in the CRM) via the bot.
- Transfer history is stored in `audit_log`.

### 7.3. "My tickets"

- "My tickets" toggle on the kanban — filter `assignee_user_id = current_user.id` (optionally plus unassigned).
- Separate `/my-tickets` page — list of the user's open tickets. In MVP — "nice to have", not mandatory.

### 7.4. Today's report

Generated on opening the "Reports" section. Shows for the current day (from 00:00 in server timezone):
- tickets created: N;
- closed (Done + Not done): M;
- transferred: K;
- currently in progress: P;
- unassigned: Q.

Admin can export to CSV (post-MVP).

## 8. Roles and Permissions

| Action | admin | agent |
|---|---|---|
| View kanban | ✅ | ✅ |
| Create ticket | ✅ | ✅ |
| Edit someone else's ticket | ✅ | ✅ (audited) |
| Take ticket into work | ✅ | ✅ |
| Transfer ticket | ✅ | ✅ |
| Delete ticket | ✅ | ❌ |
| Manage contractors | ✅ | ⚠️ create/edit yes, delete no |
| Manage CRM users | ✅ | ❌ |
| Manage statuses | ✅ | ❌ |
| View reports | ✅ | ⚠️ own only |
| System settings | ✅ | ❌ |

`viewer` role (read-only) — **out of MVP**.

## 9. User Registration and Management

- **No self-registration.** Users are created only by an admin.
- User creation: admin enters name, email, Telegram `@username`, role; generates a one-time invite link (24h TTL) or sets a temporary password.
- On first login — forced password change.
- Deactivation instead of deletion (preserves ticket history and audit).
- Password reset — via admin (MVP) or email link (post-MVP).

## 10. Data Model (high-level)

Exact fields and types — in Alembic migrations.

```
users
  ├── id, username, email, full_name, telegram_username,
  │   password_hash, role, is_active, must_change_password,
  │   created_at, last_login_at

contractors
  ├── id, name, inn, website, phone, address,
  │   has_service_contract, created_at, updated_at

departments
  ├── id, contractor_id → contractors.id, name, address

contacts
  ├── id, contractor_id → contractors.id, department_id → departments.id,
  │   full_name, telegram_id (unique), telegram_username, phone,
  │   created_at, updated_at

ticket_statuses
  ├── id, name, color, is_closed, is_default, position, is_archived

ticket_substatuses
  ├── id, status_id → ticket_statuses.id, name, position, is_archived

tickets
  ├── id, number (auto-increment), contractor_id, department_id,
  │   contact_id, assignee_user_id (nullable), status_id, substatus_id (nullable),
  │   body (text),
  │   created_by_user_id (nullable, if via web) / created_via ('bot'|'web'),
  │   created_at, updated_at, closed_at

attachments
  ├── id, ticket_id → tickets.id, filename, path, size, mime_type,
  │   uploaded_by_contact_id (nullable) / uploaded_by_user_id (nullable),
  │   created_at

audit_log
  ├── id, entity_type ('ticket'|'user'|'contractor'|…), entity_id,
  │   user_id (nullable), action ('create'|'update'|'delete'|'assign'|…),
  │   diff (JSONB), created_at
```

Indexes: `tickets(status_id, created_at DESC)`, `tickets(assignee_user_id)`, `contacts(telegram_id)`, `audit_log(entity_type, entity_id)`.

## 11. Non-Functional Requirements

### 11.1. Security

- All passwords — bcrypt (or Argon2id).
- All secrets (admin password, Telegram bot token, webhook secret, DB password) — only in `.env`, **never** in git.
- HTTPS everywhere (Let's Encrypt + Nginx).
- Rate limit on `/login` (10 attempts/min per IP).
- Session — HttpOnly + Secure cookies, 7-day TTL.
- File uploads: MIME-type check, size limit, served only to authenticated users.
- Backend port 8000 is not exposed — only through Nginx.

### 11.2. Backups

- Daily `pg_dump` at 03:00 via cron → `/var/backups/uitrix/db-YYYY-MM-DD.sql.gz`.
- 14-day retention, automatic rotation.
- Attachments — rsync to `/var/backups/uitrix/uploads/` daily.
- Monthly restore test on a clean DB (manual in the first month, automated later).

### 11.3. Audit and Logs

- All entity changes (tickets, contractors, users) — in `audit_log`.
- Application logs — structured JSON, INFO by default, ERROR with stack trace.
- Log retention — 30 days.
- Nginx logs — standard access/error, rotated via `logrotate`.

### 11.4. Privacy and 152-FZ (Russian Personal Data Law)

- The system stores personal data (full names, phones, `@username`) of contractor contacts.
- Data is stored on a server located in Russia (152-FZ requirement for Russian companies).
- An admin can export/delete all data for a specific contact (right to be forgotten).
- Backups are encrypted (GPG) before being exported off-server (post-MVP).

## 12. MVP Scope and Metrics

**MVP — included:**
- Web UI: kanban, contractors, contacts, users, statuses, basic reports.
- Telegram bot: ticket creation, attachments, status-change notifications, `/status`.
- Roles admin/agent, forced password change, no self-registration.
- Docker Compose deployment on Debian 12 + Nginx + TLS + backups.
- Audit of core actions.

**MVP success metrics (3 months after launch):**
- 3–5 pilot teams use the system daily.
- 100+ tickets processed through the bot.
- 0 lost messages/tickets (every bot message → ticket or reply).
- Uptime > 99% (measured by external monitoring).
- Backup/restore tested at least twice, RTO < 1 hour.

## 13. Explicitly Out of MVP

- SPA frontend (React/Vue). A separate development branch if needed.
- Mobile app.
- SLA timers and auto-escalation.
- Custom ticket fields.
- Multi-tenancy (one installation = one team).
- Integrations with email, calls, WhatsApp, VK.
- SSO / LDAP.
- Public API for external integrations.
- `viewer` role.
- Advanced analytics and dashboards.

## 14. Open Questions (require decision)

1. **Contact binding on message forwarding.** If client A forwards a message from client B (not their own), whose `telegram_id` is recorded? Default: whoever forwarded (`from.id` of the forwarded message is not always available in the Telegram API). Verify in practice.
2. **Password recovery.** Email link requires SMTP. In MVP — only via admin. If self-service is needed — an SMTP provider is required.
3. **Ticket priorities.** Not in MVP. If needed — a separate `priority` entity (Low/Normal/High/Urgent) + ticket field.
4. **Contact deduplication.** Manual merge in admin; automatic — post-MVP.
5. **Attachment storage.** Local directory → migrate to MinIO/S3 as the system grows. Threshold: >10 GB or >5000 files.
6. **Agent notifications.** In MVP — Telegram bot only (by user's `telegram_username`). Email notifications — post-MVP.

## 15. Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-11-07 | First raw draft (before editing). |
| 1.1 | 2026-11-07 | Added: glossary, tech stack, contacts/users split, attachments, data model, roles, security, 152-FZ, MVP metrics. Resolved: status deletion (soft-delete), no self-registration, minimal reports. |