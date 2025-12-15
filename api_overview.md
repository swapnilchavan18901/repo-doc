# APIs (Application Programming Interfaces)

## What is an API?

An **API (Application Programming Interface)** is a set of rules and protocols that allows one software application to communicate with another. APIs define how requests are made, how data is exchanged, and how responses are returned, enabling seamless integration between systems.

---

## Why APIs Are Important

- Enable communication between different applications
- Promote code reusability and modular development
- Allow integration with third-party services
- Improve scalability and maintainability of systems

---

## Types of APIs

### 1. REST APIs

- Use HTTP methods like `GET`, `POST`, `PUT`, `DELETE`
- Stateless and resource-based
- Commonly use JSON for data exchange

### 2. SOAP APIs

- Protocol-based and use XML
- Highly secure and standardized
- Used in enterprise and financial systems

### 3. GraphQL APIs

- Client specifies required data
- Reduces over-fetching and under-fetching
- Single endpoint for all queries

### 4. WebSocket APIs

- Enable real-time, bi-directional communication
- Commonly used in chat apps and live notifications

---

## Common HTTP Methods

| Method | Description          |
| ------ | -------------------- |
| GET    | Retrieve data        |
| POST   | Create new data      |
| PUT    | Update existing data |
| DELETE | Remove data          |

---

## API Request & Response

### Request Components

- **Endpoint URL**
- **HTTP Method**
- **Headers** (Authorization, Content-Type)
- **Body** (for POST/PUT requests)

### Response Components

- **Status Code** (200, 201, 400, 401, 500)
- **Response Body** (usually JSON)
- **Headers**

---

## Authentication in APIs

- API Keys
- JWT (JSON Web Tokens)
- OAuth 2.0
- Session-based authentication

---

## Best Practices

- Use proper HTTP status codes
- Version your APIs (`/api/v1`)
- Validate request data
- Implement rate limiting
- Write clear documentation

---

## Example REST API Response

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}
```
