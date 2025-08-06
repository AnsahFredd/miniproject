# AI Legal Assistant API

## 🔍 Features

- Summarize legal documents
- Answer legal questions based on context
- Upload and process legal files
- Password reset with email token verification
- JWT-based authentication
- Email confirmation on signup
- Rate limiting to prevent abuse

---

## ⚙️ Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 📦 Environment Variables

Create a `.env` file with the following:

```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET_KEY=your_jwt_secret
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
EMAIL_FROM=Your Company <your_email@gmail.com>
FRONTEND_URL=http://localhost:3000
```

---

## 📬 Endpoints

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/summarize` | POST | Summarize long legal text |
| `/ask-question` | POST | Ask a question based on a legal context |
| `/upload` | POST | Upload and process a document |
| `/auth/signup` | POST | Create new user account (sends confirmation email) |
| `/auth/confirm-email` | GET | Confirm email address via token |
| `/auth/login` | POST | Login and receive tokens |
| `/auth/refresh` | GET | Refresh expired access token |
| `/auth/reset-password/request` | POST | Request password reset via email |
| `/auth/reset-password/verify-token` | GET | Verify reset token validity |
| `/auth/reset-password/reset` | POST | Submit new password using token |

---

## 🛡️ Rate Limiting

This service uses IP-based rate limiting on sensitive routes like:
- `POST /auth/reset-password/request`
- `GET /auth/reset-password/verify-token`
- `POST /auth/reset-password/reset`
- `POST /auth/signup`
- `POST /auth/login`

By default, the limit is **5 requests per minute per IP**.  
You can configure it in `rate_limit.py`.

To apply globally:

```python
from rate_limit import RateLimiterMiddleware

app.add_middleware(RateLimiterMiddleware, max_requests=5, window_seconds=60)
```

To scope it only to specific routes, update the middleware logic to match paths.

---

## ✅ Unit Tests

Run tests from the project root:

```bash
pytest tests/test_auth_service.py
```

Covers:
- Requesting reset token
- Verifying token
- Resetting password
- Expired or invalid tokens

---

## 🧩 Folder Structure

```
app/
├── api/                     # Route handlers
├── core/                    # Config, utilities
├── services/                # Business logic (auth, embeddings, summarization)
├── models/                  # MongoDB models
├── schemas/                 # Pydantic request/response models
├── tasks/                   # Async Celery tasks (if any)
tests/
├── test_auth_service.py     # Unit tests for password reset flow
rate_limit.py                # Rate limiter middleware
```

---

## 🔐 Security Notes

- Use strong JWT secrets and keep them out of version control.
- Rate limiting helps prevent brute-force attacks on auth routes.
- Reset emails do not disclose whether a user exists (for privacy).
- Email confirmation ensures that users verify their identity before logging in.
