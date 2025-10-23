# 🔗 URL Shortener & Management API (FastAPI)

A powerful, token-based URL shortener and management API built using **FastAPI**.  
This service allows users to create short URLs, protect them with passwords, and manage them — including pausing, resuming, deleting, and changing links — all through authenticated endpoints.

---

## 🚀 Features

- Create short URLs with optional passwords  
- Secure authentication using **Bearer Tokens**  
- Change, pause, resume, or delete URLs  
- Reset hit counters for URLs  
- Change passwords for existing URLs  
- Token validation and refresh endpoints  
- Health check endpoint for monitoring  

---

## 🧩 Tech Stack

- **FastAPI** — Web framework  
- **Pydantic** — Data validation  
- **Python 3.11+**  
- **JWT / Bearer Token** authentication  

---

## ⚙️ Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/tanmandal/Short-URL.git
cd url-shortener-api
pip install -r requirements.txt
````

---

## ▶️ Running the Server

Start the FastAPI application with:

```bash
uvicorn main:app --reload
```

By default, the server runs at:

```
http://127.0.0.1:8000
```

Access interactive API documentation at:

* Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔐 Authentication

All management routes (e.g., `/delete`, `/pause`, `/resume`, etc.) require an **HTTP Bearer token**.
You can obtain a token using the `/login` endpoint after creating a URL.

Example header:

```
Authorization: Bearer <your_token_here>
```

---

## 📚 API Endpoints

### 🟢 Public Endpoints

| Method | Endpoint      | Description            |
| ------ | ------------- | ---------------------- |
| `GET`  | `/`           | Root endpoint          |
| `POST` | `/create`     | Create a new short URL |
| `POST` | `/login`      | Login and get token    |
| `GET`  | `/health`     | Health check endpoint  |
| `GET`  | `/{url_code}` | Redirect to long URL   |

---

### 🔒 Protected Endpoints (Require Token)

| Method   | Endpoint           | Description                  |
| -------- | ------------------ | ---------------------------- |
| `POST`   | `/change_password` | Change password for URL      |
| `DELETE` | `/delete`          | Delete a URL entry           |
| `PATCH`  | `/pause`           | Pause a URL (disable usage)  |
| `PATCH`  | `/resume`          | Resume a paused URL          |
| `PATCH`  | `/reset_hits`      | Reset hit counter            |
| `PATCH`  | `/change_url`      | Update destination URL       |
| `GET`    | `/details`         | Get details for URL          |
| `GET`    | `/validate_token`  | Validate authentication      |
| `GET`    | `/refresh_token`   | Refresh expired access token |

---

## 🧾 Schemas

### URLEntry

| Field      | Type   | Required | Description                     |
| ---------- | ------ | -------- | ------------------------------- |
| `url_code` | string | ✅        | Unique code (alias) for the URL |
| `url_pass` | string | ❌        | Optional password               |
| `url`      | string | ✅        | The destination URL             |

### LoginEntry

| Field      | Type   | Required | Description                  |
| ---------- | ------ | -------- | ---------------------------- |
| `url_code` | string | ✅        | URL alias                    |
| `url_pass` | string | ✅        | Password associated with URL |

### ResetEntry

| Field          | Type   | Required | Description  |
| -------------- | ------ | -------- | ------------ |
| `url_code`     | string | ✅        | URL alias    |
| `old_url_pass` | string | ✅        | Old password |
| `new_url_pass` | string | ✅        | New password |

---

## 📦 Example Request Bodies

### Create URL (`POST /create`)

```json
{
  "url_code": "myalias",
  "url_pass": "mypassword",
  "url": "https://example.com"
}
```

### Login (`POST /login`)

```json
{
  "url_code": "myalias",
  "url_pass": "mypassword"
}
```

### Change Password (`POST /change_password`)

```json
{
  "url_code": "myalias",
  "old_url_pass": "oldpass",
  "new_url_pass": "newpass"
}
```

---

## 📤 Example Responses

### ✅ Successful Creation (`201 Created`)

```json
{
  "message": "Short URL created successfully",
  "short_url": "http://127.0.0.1:8000/myalias"
}
```

### ❌ Invalid Credentials (`401 Unauthorized`)

```json
{
  "detail": "Invalid credentials"
}
```

---

## 🩺 Health Check

To verify the API is running:

```bash
GET /health
```

Response:

```json
{"status": "ok"}
```

---

## 🧠 Notes

* Each `url_code` uniquely identifies a shortened URL.
* Passwords are optional for creation but required for login.
* Token authentication ensures secure URL management.
* Validation errors return standard FastAPI `422` responses.
* Protected endpoints require Bearer tokens for authorization.

---

## 🧾 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome!
Please open an issue or submit a pull request for any feature requests or bug fixes.

---

## 💬 Contact

**Author:** Tanmay Mandal
**GitHub:** [@tanmandal](https://github.com/tanmandal)

---

> Built with ❤️ using [FastAPI](https://fastapi.tiangolo.com/)
