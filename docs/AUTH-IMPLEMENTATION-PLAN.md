# Auth Feature Implementation Plan — Email Confirmation + Password Reset

## Current State

- **User model**: `id, email, hashed_password, created_at, updated_at` — no `is_active`, no token tracking
- **Auth router**: `/register` (creates user, returns them), `/login` (JWT), `/me`, `/reset-password` (stub), `/reset-password/confirm` (stub)
- **Frontend**: LoginPage with register/login toggle. After register → auto-login. No email confirmation, no forgot-password UI
- **Email**: No email infrastructure exists in this project.

## Email Provider: Sweego

- **API endpoint**: `POST https://api.sweego.io/send`
- **Auth header**: `Api-Key: *** **Sender domain**: `noreply@support.jonaskrauss.de` (verified subdomain `support.jonaskrauss.de`)
- **Body format**:
  ```json
  {
    "channel": "email",
    "provider": "sweego",
    "recipients": [{"email": "user@example.com"}],
    "from": {"name": "Tracking Success", "email": "noreply@support.jonaskrauss.de"},
    "subject": "Subject",
    "message-txt": "Plain text body",
    "campaign-type": "transac"
  }
  ```
- **1Password item**: `op://hermine/sweego-api-key/credential`
- **No new Python dep needed** — use stdlib `urllib.request` to POST JSON to Sweego API. The backend is async but email sending is a fire-and-forget operation; we run it via `asyncio.to_thread()` to avoid blocking the event loop.

## Requirements

1. **Email confirmation on register**: New users get a confirmation email with a token-link. Until confirmed, login is blocked. After confirming, they can login.
2. **Forgot password**: "Forgot Password" button on login page. User enters email. If email exists → send reset email with token-link. If not → tell the user that email doesn't exist. User clicks link → can set new password → can login.

## Architecture

### Backend

- **Token storage**: Database table `email_tokens` with `id, user_id, token_hash, token_type (confirm|reset), expires_at, used_at`. We store the **sha256 hash** of the token, not the raw token — so a DB leak doesn't expose valid tokens. The raw token is only known to the user via the email link.
- **Token generation**: `secrets.token_urlsafe(32)` — stdlib, 43 chars, URL-safe.
- **Token TTL**: Confirm = 24h, Reset = 1h.
- **User model change**: Add `is_active: bool = False` column. Login checks `is_active`.
- **Email sending**: stdlib `urllib.request` to POST to Sweego API, wrapped in `asyncio.to_thread()`. No new dep.
- **New endpoints**:
  - `POST /api/auth/register` → modified: creates user `is_active=False`, sends confirmation email
  - `GET /api/auth/confirm/{token}` → validates token, sets `is_active=True`
  - `POST /api/auth/forgot-password` → takes email, checks existence, sends reset email if exists, tells user if not
  - `POST /api/auth/reset-password/confirm` → takes token + new_password, validates token, updates password
  - `POST /api/auth/resend-confirmation` → resends confirmation email if user is still inactive

### Frontend

- **LoginPage**: Add "Passwort vergessen?" link below the login form. Add status messages for confirmation-sent, account-confirmed, password-reset, etc.
- **New routes**: `/confirm-email` (shows pending state, processes token from URL), `/reset-password` (processes token from URL, shows new-password form)
- **api.ts**: Add `confirmEmail(token)`, `forgotPassword(email)`, `resetPasswordConfirm(token, newPassword)`, `resendConfirmation(email)`
- **useAuth**: Register no longer auto-logs in. Instead shows "check your email" message.

### Email content

- **Confirmation email**: German (app is German). Subject: "E-Mail bestätigen — Tracking Success". Body: plain text with link `https://tracking-success.stage.jonaskrauss.de/confirm-email?token=XXX`
- **Reset email**: Subject: "Passwort zurücksetzen — Tracking Success". Body: plain text with link `https://tracking-success.stage.jonaskrauss.de/reset-password?token=XXX`
- **Base URL**: from env var `APP_BASE_URL` (staging: `https://tracking-success.stage.jonaskrauss.de`, prod: `https://tracking-success.jonaskrauss.de`)