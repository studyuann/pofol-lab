---
title: "Docker Compose로 풀스택 앱 구성하기"
date: 2026-08-02
tags: ["메가존클라우드 MSP 솔루션 아키텍트", "Docker"]
is_public: true
draft: false
---

# Docker Compose로 풀스택 앱 구성하기

## 📋 학습 목표

* 풀스택 애플리케이션의 구조와 구성 요소를 이해한다

* Docker Compose로 복잡한 멀티 서비스 환경을 구축한다

* 프런트엔드, 백엔드, 데이터베이스를 통합한 완전한 시스템을 만든다

* 서비스 간 통신과 데이터 흐름을 설계한다

* 개발부터 배포까지의 전체 워크플로우를 구현한다

---

## 1. 풀스택 애플리케이션 아키텍처 이해

### 1.1 풀스택 애플리케이션이란?

### 🏗️ 풀스택 구성 요소

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React/Vue)   │◄──►│   (Node.js)     │◄──►│   (MySQL)       │
│   Port: 3000    │    │   Port: 5000    │    │   Port: 3306    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌───────────────────────────────────────────────────────────────┐
│                         Docker Network                        │
└───────────────────────────────────────────────────────────────┘
```

**주요 구성 요소:**

* **Frontend**: 사용자 인터페이스 (React, Vue, Angular)

* **Backend**: API 서버 (Node.js, Python, Java)

* **Database**: 데이터 저장소 (MySQL, PostgreSQL, MongoDB)

* **Cache**: 성능 향상 (Redis)

* **Proxy**: 리버스 프록시 (Nginx)

### 1.2 우리가 만들 풀스택 앱 - "할 일 관리 시스템"

### 🎯 프로젝트 개요

* **Frontend**: React 기반 SPA

* **Backend**: Node.js + Express API

* **Database**: MySQL

* **Cache**: Redis

* **Proxy**: Nginx

### 기능 요구사항

* 사용자 회원가입/로그인

* 할 일 CRUD (생성, 조회, 수정, 삭제)

* 실시간 업데이트

* 반응형 웹 디자인

---

## 2. 프로젝트 구조 설계

### 2.1 디렉토리 구조

```
fullstack-todo/
├── compose.yml                # Docker Compose 설정
├── .env                       # 환경변수
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
|   |     |- index.html 
│   └── src/
│       ├── App.js
│       ├── App.css
|       |-- index.js 
|       |-- index.css 
│       ├── components/
│       └── services/
├── backend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app.js
│   │   ├── routes/
│   │   ├── models/
│   │   └── middleware/
│   └── init-db/
│       └── schema.sql
└── data/                      # 데이터 지속성을 위한 폴더
```

### 2.2 Docker Compose 메인 설정

### compose.yml

```
services:
  # Nginx 리버스 프록시
  nginx:
    build: ./nginx
    ports:
      - "80:80"
    depends_on:
      - frontend
      - backend
    networks:
      - app-network
    restart: unless-stopped

  # React 프런트엔드
  frontend:
    build:
      context: ./frontend
      target: development
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=/api
      - CHOKIDAR_USEPOLLING=true
    networks:
      - app-network
    restart: unless-stopped

  # Node.js 백엔드
  backend:
    build: ./backend
    volumes:
      - ./backend/src:/app/src
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DB_HOST=database
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
      - REDIS_HOST=redis
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network
    restart: unless-stopped

  # MySQL 데이터베이스
  database:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/init-db:/docker-entrypoint-initdb.d
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis 캐시
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Adminer (데이터베이스 관리 도구)
  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge

volumes:
  mysql_data:
  redis_data:
```

### 2.3 환경 변수 설정

### .env

```
# 데이터베이스 설정
DB_ROOT_PASSWORD=rootpassword123
DB_NAME=todoapp
DB_USER=todouser
DB_PASSWORD=todopassword123

# JWT 시크릿
JWT_SECRET=your-super-secret-jwt-key-here

# 환경 설정
NODE_ENV=development
REACT_APP_API_URL=http://localhost/api
```

---

## 3. Nginx 리버스 프록시 설정

### 3.1 Nginx Dockerfile

### nginx/Dockerfile

```
FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3.2 Nginx 설정 파일

### nginx/nginx.conf

```
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream backend {
        server backend:5000;
    }

    server {
        listen 80;
        server_name localhost;

        # 정적 파일 설정
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket 지원 (React 개발 서버용)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";

            # 타임아웃 설정
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # API 라우팅
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # CORS 헤더
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";

            # 타임아웃 설정
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;

            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }

        # 헬스체크 엔드포인트
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 4. 백엔드 API 서버 구현

### 4.1 Backend Dockerfile

### backend/Dockerfile

```
FROM node:18-alpine

WORKDIR /app

# 의존성 설치를 위한 package.json 복사
COPY package*.json ./
RUN npm ci

# 애플리케이션 코드 복사
COPY . .

EXPOSE 5000

# 개발 모드로 실행 (nodemon 사용)
CMD ["npm", "run", "dev"]
```

### 4.2 Package.json 설정

### backend/package.json

```
{
  "name": "todo-backend",
  "version": "1.0.0",
  "description": "Todo App Backend API",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "dev": "nodemon src/app.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "mysql2": "^3.6.0",
    "redis": "^4.6.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "joi": "^17.9.0",
    "helmet": "^7.0.0",
    "express-rate-limit": "^6.8.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0",
    "jest": "^29.0.0"
  }
}
```

이미지 생성전에 npm install 실행

### 4.3 Express 애플리케이션

### backend/src/app.js

```
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const mysql = require('mysql2/promise');
const redis = require('redis');

const app = express();
const PORT = process.env.PORT || 5000;

// 미들웨어 설정
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json());

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15분
  max: 100 // 최대 100 요청
});
app.use(limiter);

// 데이터베이스 연결 설정
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'password',
  database: process.env.DB_NAME || 'todoapp',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

let db;
let redisClient;

// 데이터베이스 연결
async function initializeDatabase() {
  try {
    db = mysql.createPool(dbConfig);
    console.log('✅ MySQL connected successfully');
  } catch (error) {
    console.error('❌ MySQL connection failed:', error);
    process.exit(1);
  }
}

// Redis 연결
async function initializeRedis() {
  try {
    redisClient = redis.createClient({
      url: `redis://${process.env.REDIS_HOST || 'localhost'}:6379`
    });

    await redisClient.connect();
    console.log('✅ Redis connected successfully');
  } catch (error) {
    console.error('❌ Redis connection failed:', error);
  }
}

// 라우트 정의
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// 할 일 목록 조회
app.get('/todos', async (req, res) => {
  try {
    // Redis 캐시 확인
    const cached = await redisClient?.get('todos');
    if (cached) {
      return res.json(JSON.parse(cached));
    }

    // 데이터베이스에서 조회
    const [rows] = await db.execute(
      'SELECT id, title, description, completed, created_at, updated_at FROM todos ORDER BY created_at DESC'
    );

    // Redis에 캐시 저장 (5분)
    await redisClient?.setEx('todos', 300, JSON.stringify(rows));

    res.json(rows);
  } catch (error) {
    console.error('Error fetching todos:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 할 일 생성
app.post('/todos', async (req, res) => {
  try {
    const { title, description = '' } = req.body;

    if (!title || title.trim().length === 0) {
      return res.status(400).json({ error: 'Title is required' });
    }

    const [result] = await db.execute(
      'INSERT INTO todos (title, description) VALUES (?, ?)',
      [title.trim(), description.trim()]
    );

    // 캐시 무효화
    await redisClient?.del('todos');

    res.status(201).json({
      id: result.insertId,
      title: title.trim(),
      description: description.trim(),
      completed: false,
      created_at: new Date()
    });
  } catch (error) {
    console.error('Error creating todo:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 할 일 수정
app.put('/todos/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, completed } = req.body;

    const [result] = await db.execute(
      'UPDATE todos SET title = ?, description = ?, completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [title, description, completed, id]
    );

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }

    // 캐시 무효화
    await redisClient?.del('todos');

    res.json({ message: 'Todo updated successfully' });
  } catch (error) {
    console.error('Error updating todo:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 할 일 삭제
app.delete('/todos/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const [result] = await db.execute('DELETE FROM todos WHERE id = ?', [id]);

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }

    // 캐시 무효화
    await redisClient?.del('todos');

    res.json({ message: 'Todo deleted successfully' });
  } catch (error) {
    console.error('Error deleting todo:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// 에러 핸들링 미들웨어
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 핸들러
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// 서버 시작
async function startServer() {
  await initializeDatabase();
  await initializeRedis();

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
  });
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  await db?.end();
  await redisClient?.disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down gracefully');
  await db?.end();
  await redisClient?.disconnect();
  process.exit(0);
});

startServer().catch(console.error);
```

### 4.4 데이터베이스 스키마

### backend/init-db/schema.sql

```
-- 할 일 테이블 생성
CREATE TABLE IF NOT EXISTS todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 사용자 테이블 (향후 확장용)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 샘플 데이터 삽입
INSERT INTO todos (title, description, completed) VALUES
('Docker Compose 학습하기', 'Docker Compose로 풀스택 애플리케이션 구성 방법 익히기', false),
('React 앱 개발', '할 일 관리 시스템 프런트엔드 개발', false),
('API 서버 구축', 'Node.js와 Express로 REST API 구현', true),
('데이터베이스 설계', 'MySQL을 사용한 데이터 모델링', true);

-- 인덱스 생성
CREATE INDEX idx_todos_created_at ON todos(created_at);
CREATE INDEX idx_todos_completed ON todos(completed);
```

---

## 5. 프런트엔드 React 애플리케이션

### 5.1 Frontend Dockerfile

### frontend/Dockerfile

```
# 개발 환경용 멀티스테이지 빌드
FROM node:18-alpine AS base

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci

# 개발 스테이지
FROM base AS development
WORKDIR /app
COPY . .
EXPOSE 3000
ENV WATCHPACK_POLLING=true
CMD ["npm", "start"]

# 프로덕션 빌드 스테이지
FROM base AS builder
WORKDIR /app
COPY . .
RUN npm run build

# 프로덕션 스테이지
FROM nginx:alpine AS production
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 5.2 Package.json 설정

### frontend/package.json

```
{
  "name": "todo-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.5.0",
    "react-query": "^3.39.0",
    "react-hot-toast": "^2.4.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://backend:5000"
}
```

이미지 생성 전에 npm install 실행

### 5.3 메인 React 컴포넌트

### public/index.html

```
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Docker Compose 풀스택 할 일 관리 애플리케이션"
    />
    <title>할 일 관리 - Todo App</title>
  </head>
  <body>
    <noscript>이 애플리케이션을 실행하려면 JavaScript를 활성화해야 합니다.</noscript>
    <div id="root"></div>
  </body>
</html>
```

### frontend/src/App.js

```
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || '/api';

// API 클라이언트 설정
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTodo, setNewTodo] = useState({ title: '', description: '' });

  // 할 일 목록 조회
  const fetchTodos = async () => {
    try {
      setLoading(true);
      const response = await api.get('/todos');
      setTodos(response.data);
    } catch (error) {
      console.error('Failed to fetch todos:', error);
      toast.error('할 일 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 할 일 추가
  const addTodo = async (e) => {
    e.preventDefault();

    if (!newTodo.title.trim()) {
      toast.error('제목을 입력해주세요.');
      return;
    }

    try {
      const response = await api.post('/todos', newTodo);
      setTodos([response.data, ...todos]);
      setNewTodo({ title: '', description: '' });
      toast.success('할 일이 추가되었습니다.');
    } catch (error) {
      console.error('Failed to add todo:', error);
      toast.error('할 일 추가에 실패했습니다.');
    }
  };

  // 할 일 완료 상태 변경
  const toggleTodo = async (id, completed) => {
    try {
      const todo = todos.find(t => t.id === id);
      await api.put(`/todos/${id}`, {
        ...todo,
        completed: !completed
      });

      setTodos(todos.map(todo =>
        todo.id === id ? { ...todo, completed: !completed } : todo
      ));

      toast.success(completed ? '할 일을 미완료로 변경했습니다.' : '할 일을 완료했습니다.');
    } catch (error) {
      console.error('Failed to toggle todo:', error);
      toast.error('할 일 상태 변경에 실패했습니다.');
    }
  };

  // 할 일 삭제
  const deleteTodo = async (id) => {
    if (!window.confirm('정말로 삭제하시겠습니까?')) {
      return;
    }

    try {
      await api.delete(`/todos/${id}`);
      setTodos(todos.filter(todo => todo.id !== id));
      toast.success('할 일이 삭제되었습니다.');
    } catch (error) {
      console.error('Failed to delete todo:', error);
      toast.error('할 일 삭제에 실패했습니다.');
    }
  };

  // 컴포넌트 마운트 시 할 일 목록 조회
  useEffect(() => {
    fetchTodos();
  }, []);

  return (
    <div className="App">
      <Toaster position="top-right" />

      <header className="App-header">
        <h1>📝 할 일 관리</h1>
        <p>Docker Compose로 구성한 풀스택 애플리케이션</p>
      </header>

      <main className="main-content">
        {/* 할 일 추가 폼 */}
        <section className="add-todo-section">
          <h2>새 할 일 추가</h2>
          <form onSubmit={addTodo} className="add-todo-form">
            <div className="form-group">
              <input
                type="text"
                placeholder="할 일 제목을 입력하세요"
                value={newTodo.title}
                onChange={(e) => setNewTodo({ ...newTodo, title: e.target.value })}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <textarea
                placeholder="상세 설명 (선택사항)"
                value={newTodo.description}
                onChange={(e) => setNewTodo({ ...newTodo, description: e.target.value })}
                className="form-textarea"
                rows="3"
              />
            </div>
            <button type="submit" className="btn btn-primary">
              추가하기
            </button>
          </form>
        </section>

        {/* 할 일 목록 */}
        <section className="todos-section">
          <h2>할 일 목록 ({todos.length}개)</h2>

          {loading ? (
            <div className="loading">로딩 중...</div>
          ) : todos.length === 0 ? (
            <div className="empty-state">
              <p>할 일이 없습니다. 새로운 할 일을 추가해보세요!</p>
            </div>
          ) : (
            <div className="todos-grid">
              {todos.map(todo => (
                <div
                  key={todo.id}
                  className={`todo-card ${todo.completed ? 'completed' : ''}`}
                >
                  <div className="todo-content">
                    <h3 className="todo-title">{todo.title}</h3>
                    {todo.description && (
                      <p className="todo-description">{todo.description}</p>
                    )}
                    <div className="todo-meta">
                      <span className="todo-date">
                        생성일: {new Date(todo.created_at).toLocaleDateString('ko-KR')}
                      </span>
                      {todo.updated_at !== todo.created_at && (
                        <span className="todo-date">
                          수정일: {new Date(todo.updated_at).toLocaleDateString('ko-KR')}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="todo-actions">
                    <button
                      onClick={() => toggleTodo(todo.id, todo.completed)}
                      className={`btn ${todo.completed ? 'btn-warning' : 'btn-success'}`}
                    >
                      {todo.completed ? '미완료' : '완료'}
                    </button>
                    <button
                      onClick={() => deleteTodo(todo.id)}
                      className="btn btn-danger"
                    >
                      삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="App-footer">
        <p>🐳 Docker Compose 풀스택 애플리케이션 예제</p>
        <div className="tech-stack">
          <span>React</span>
          <span>Node.js</span>
          <span>MySQL</span>
          <span>Redis</span>
          <span>Nginx</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
```

### frontend/src/index.js

```
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### frontend/src/index.css

```
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

* {
  box-sizing: border-box;
}
```

### 5.4 CSS 스타일링

### frontend/src/App.css

```
.App {
  text-align: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.App-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  border-radius: 15px;
  color: white;
  margin-bottom: 40px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.App-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5rem;
  font-weight: 600;
}

.App-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.main-content {
  max-width: 800px;
  margin: 0 auto;
}

.add-todo-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  margin-bottom: 40px;
}

.add-todo-section h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

.add-todo-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  text-align: left;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 16px;
  font-family: inherit;
  transition: border-color 0.3s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
  transform: translateY(-1px);
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-warning:hover {
  background: #e0a800;
  transform: translateY(-1px);
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
  transform: translateY(-1px);
}

.todos-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.todos-section h2 {
  margin-bottom: 25px;
  color: #333;
  font-size: 1.5rem;
}

.loading {
  padding: 40px;
  color: #666;
  font-size: 18px;
}

.empty-state {
  padding: 60px 20px;
  color: #666;
}

.empty-state p {
  font-size: 18px;
  margin: 0;
}

.todos-grid {
  display: grid;
  gap: 20px;
}

.todo-card {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.3s ease;
}

.todo-card:hover {
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.todo-card.completed {
  opacity: 0.7;
  border-color: #28a745;
  background: #f8fff8;
}

.todo-card.completed .todo-title {
  text-decoration: line-through;
  color: #666;
}

.todo-content {
  flex: 1;
  text-align: left;
}

.todo-title {
  margin: 0 0 8px 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.todo-description {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.todo-meta {
  font-size: 0.85rem;
  color: #999;
}

.todo-date {
  margin-right: 15px;
}

.todo-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.todo-actions .btn {
  padding: 8px 16px;
  font-size: 14px;
}

.App-footer {
  margin-top: 50px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 15px;
  color: #666;
}

.App-footer p {
  margin: 0 0 15px 0;
  font-size: 1.1rem;
}

.tech-stack {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.tech-stack span {
  background: #667eea;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .App {
    padding: 15px;
  }

  .App-header {
    padding: 30px 20px;
  }

  .App-header h1 {
    font-size: 2rem;
  }

  .add-todo-section,
  .todos-section {
    padding: 20px;
  }

  .todo-card {
    flex-direction: column;
    gap: 15px;
  }

  .todo-actions {
    align-self: stretch;
  }

  .todo-actions .btn {
    flex: 1;
  }

  .tech-stack {
    gap: 10px;
  }
}
```

---

## 6. 서비스 간 통신 및 데이터 흐름

### 6.1 데이터 흐름 다이어그램

```
사용자 브라우저
    ↓ HTTP Request (포트 80)
Nginx (리버스 프록시)
    ↓ /api/* → Backend (포트 5000)
    ↓ /* → Frontend (포트 3000)
Node.js API 서버
    ↓ SQL Query (포트 3306)
    ↓ Cache Check (포트 6379)
MySQL Database ←→ Redis Cache
```

### 6.2 환경별 설정 파일

### 개발환경 오버라이드 (compose.override.yml)

```
# 개발 환경용 오버라이드 설정
services:
  frontend:
    build:
      target: development
    volumes:
      - ./frontend/src:/app/src
      - /app/node_modules
    environment:
      - FAST_REFRESH=false
      - CHOKIDAR_USEPOLLING=true

  backend:
    volumes:
      - ./backend/src:/app/src
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: npm run dev

  database:
    ports:
      - "3306:3306"  # 개발시 직접 접근 가능
    environment:
      MYSQL_GENERAL_LOG: 1

  redis:
    ports:
      - "6379:6379"  # 개발시 직접 접근 가능
```

### 프로덕션 설정 (compose.prod.yml)

```
# 프로덕션 환경 설정
services:
  nginx:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  frontend:
    build:
      target: production
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  backend:
    environment:
      - NODE_ENV=production
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    # 개발용 볼륨 마운트 제거

  database:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    volumes:
      - /opt/mysql-data:/var/lib/mysql  # 외부 스토리지
    # 포트 노출 제거 (보안)

  redis:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 256M
    # 포트 노출 제거 (보안)

  adminer:
    profiles:
      - tools  # 프로덕션에서는 기본적으로 비활성화

volumes:
  mysql_data:
    external: true
  redis_data:
    external: true
```

---

## 7. 실습 과제

### 📝 기본 실습

### 실습 1: 풀스택 애플리케이션 구축

**목표:** 제공된 코드로 완전한 할 일 관리 시스템 구축

```
# 1단계: 프로젝트 디렉토리 생성
mkdir fullstack-todo
cd fullstack-todo

# 2단계: 디렉토리 구조 생성
mkdir -p nginx frontend/src backend/src backend/init-db

# 3단계: 각 파일들 생성 (위에서 제공된 코드 사용)
# - compose.yml
# - .env
# - nginx/Dockerfile, nginx/nginx.conf
# - frontend/Dockerfile, frontend/package.json, frontend/src/App.js, frontend/src/App.css
# - backend/Dockerfile, backend/package.json, backend/src/app.js, backend/init-db/schema.sql

frontend와 backend 디렉토리에서 npm init -y ,  npm install 수행
# 4단계: 전체 스택 실행
docker compose up -d

# 5단계: 서비스 상태 확인
docker compose ps
curl http://localhost/api/health
curl http://localhost/api/todos

# 6단계: 브라우저에서 http://localhost 접속하여 기능 테스트
```

### 실습 2: 기능 확장

**목표:** 할 일 우선순위 및 마감일 기능 추가

```
-- 데이터베이스 스키마 수정
ALTER TABLE todos ADD COLUMN priority ENUM('low', 'medium', 'high') DEFAULT 'medium';
ALTER TABLE todos ADD COLUMN due_date DATE NULL;

-- 인덱스 추가
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_todos_due_date ON todos(due_date);
```

### 🚀 심화 실습

### 실습 3: 사용자 인증 시스템

**목표:** JWT 기반 회원가입/로그인 구현

```
// 백엔드에 인증 미들웨어 추가
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

// 회원가입 API
app.post('/auth/register', async (req, res) => {
  const { email, password, name } = req.body;

  try {
    const hashedPassword = await bcrypt.hash(password, 10);

    const [result] = await db.execute(
      'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
      [email, hashedPassword, name]
    );

    const token = jwt.sign(
      { userId: result.insertId, email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.status(201).json({
      token,
      user: { id: result.insertId, email, name }
    });
  } catch (error) {
    res.status(400).json({ error: 'Registration failed' });
  }
});

// 로그인 API
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;

  try {
    const [users] = await db.execute(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );

    if (users.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = users[0];
    const validPassword = await bcrypt.compare(password, user.password_hash);

    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      token,
      user: { id: user.id, email: user.email, name: user.name }
    });
  } catch (error) {
    res.status(500).json({ error: 'Login failed' });
  }
});
```

---

## 8. 모니터링 및 로깅

### 8.1 헬스체크 구현

### 종합 헬스체크 엔드포인트

```
// backend/src/app.js에 추가
app.get('/health/detailed', async (req, res) => {
  const healthCheck = {
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    status: 'healthy',
    checks: {
      database: 'unknown',
      redis: 'unknown',
      memory: 'unknown'
    }
  };

  try {
    // 데이터베이스 연결 확인
    await db.execute('SELECT 1');
    healthCheck.checks.database = 'healthy';
  } catch (error) {
    healthCheck.checks.database = 'unhealthy';
    healthCheck.status = 'unhealthy';
  }

  try {
    // Redis 연결 확인
    await redisClient?.ping();
    healthCheck.checks.redis = 'healthy';
  } catch (error) {
    healthCheck.checks.redis = 'unhealthy';
  }

  // 메모리 사용량 확인
  const memUsage = process.memoryUsage();
  const memUsagePercent = (memUsage.rss / 1024 / 1024 / 1024).toFixed(2);

  healthCheck.checks.memory = memUsagePercent < 1 ? 'healthy' : 'warning';
  healthCheck.memory = {
    rss: `${memUsagePercent}GB`,
    heapUsed: `${(memUsage.heapUsed / 1024 / 1024).toFixed(2)}MB`,
    heapTotal: `${(memUsage.heapTotal / 1024 / 1024).toFixed(2)}MB`
  };

  const statusCode = healthCheck.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthCheck);
});
```

### 8.2 모니터링 스택 추가

### compose.monitoring.yml

```
# 모니터링 서비스 추가
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - app-network
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

---

## 9. 운영 환경 배포

### 9.1 프로덕션 배포 스크립트

### deploy.sh

```
#!/bin/bash
set -e

echo "🚀 Starting production deployment..."

# 환경 설정
ENVIRONMENT=${1:-production}
VERSION=$(git rev-parse --short HEAD)

# 1. 이미지 빌드
echo "🔨 Building production images..."
docker compose -f compose.yml -f compose.prod.yml build

# 2. 데이터베이스 백업 (기존 데이터가 있는 경우)
echo "💾 Creating database backup..."
if docker compose ps database | grep -q "Up"; then
    docker compose exec database mysqldump -u root -p${DB_ROOT_PASSWORD} --all-databases > backup_$(date +%Y%m%d_%H%M%S).sql
fi

# 3. 프로덕션 배포
echo "🎯 Deploying to production..."
docker compose -f compose.yml -f compose.prod.yml up -d

# 4. 헬스체크
echo "❤️ Running health checks..."
sleep 30

for i in {1..5}; do
    if curl -f http://localhost/api/health; then
        echo "✅ Deployment successful!"
        break
    else
        echo "⏳ Waiting for services... (attempt $i/5)"
        if [ $i -eq 5 ]; then
            echo "❌ Deployment failed! Rolling back..."
            docker compose -f compose.yml -f compose.prod.yml down
            exit 1
        fi
        sleep 10
    fi
done

echo "🎉 Production deployment completed!"
```

---

## 10. 트러블슈팅 가이드

### 10.1 자주 발생하는 문제들

### 서비스 간 통신 문제

```
# 네트워크 연결 확인
docker compose exec frontend ping backend
docker compose exec backend ping database

# DNS 해결 확인
docker compose exec frontend nslookup backend

# 포트 확인
docker compose exec backend netstat -tulpn
```

### 데이터베이스 연결 문제

```
# MySQL 상태 확인
docker compose exec database mysqladmin -u root -p status

# 연결 테스트
docker compose exec database mysql -u todouser -ptodopassword123 todoapp -e "SELECT 1;"

# 로그 확인
docker compose logs database
```

### 10.2 종합 진단 스크립트

```
#!/bin/bash
# debug.sh

echo "🔍 Full Stack Application Diagnosis"
echo "================================="

# 1. 서비스 상태
echo "📊 Service Status:"
docker compose ps

# 2. 네트워크 연결
echo -e "\n🌐 Network Connectivity:"
docker compose exec -T frontend ping -c 2 backend 2>/dev/null && echo "✅ Frontend → Backend" || echo "❌ Frontend → Backend"
docker compose exec -T backend ping -c 2 database 2>/dev/null && echo "✅ Backend → Database" || echo "❌ Backend → Database"
docker compose exec -T backend ping -c 2 redis 2>/dev/null && echo "✅ Backend → Redis" || echo "❌ Backend → Redis"

# 3. 헬스체크
echo -e "\n❤️ Health Checks:"
curl -s http://localhost/api/health > /dev/null && echo "✅ API Health" || echo "❌ API Health"
curl -s http://localhost > /dev/null && echo "✅ Frontend" || echo "❌ Frontend"

# 4. 리소스 사용량
echo -e "\n💾 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 5. 로그 오류 검사
echo -e "\n📜 Recent Errors:"
docker compose logs --tail=20 | grep -i error || echo "No errors found"
```

---

## 11. 베스트 프랙티스

### 11.1 개발 효율성 팁

```
# 자주 사용하는 명령어 별칭
alias dcup='docker compose up -d'
alias dcdown='docker compose down'
alias dclogs='docker compose logs -f'
alias dcbuild='docker compose build'
alias dcrestart='docker compose restart'

# 전체 스택 재시작 스크립트
#!/bin/bash
# restart-stack.sh
echo "🔄 Restarting full stack..."
docker compose down
docker compose build
docker compose up -d
echo "✅ Stack restarted successfully!"
```

### 11.2 보안 고려사항

```
// 입력 검증 강화
const Joi = require('joi');

const todoSchema = Joi.object({
  title: Joi.string().min(1).max(255).required(),
  description: Joi.string().max(1000).allow(''),
  completed: Joi.boolean(),
  priority: Joi.string().valid('low', 'medium', 'high').default('medium')
});

// Rate Limiting 세분화
const createLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1시간
  max: 10, // 생성은 시간당 10개로 제한
  message: '너무 많은 할 일을 생성했습니다. 잠시 후 다시 시도해주세요.'
});
```

### 11.3 성능 최적화

```
// React 성능 최적화
import React, { memo, useCallback, useMemo } from 'react';

const TodoItem = memo(({ todo, onToggle, onDelete }) => {
  const handleToggle = useCallback(() => {
    onToggle(todo.id, todo.completed);
  }, [todo.id, todo.completed, onToggle]);

  const formattedDate = useMemo(() => {
    return new Date(todo.created_at).toLocaleDateString('ko-KR');
  }, [todo.created_at]);

  return (
    <div className={`todo-card ${todo.completed ? 'completed' : ''}`}>
      {/* 컴포넌트 내용 */}
    </div>
  );
});
```

---

### 유용한 명령어 모음

```
# 개발 워크플로우
alias ddev='docker compose up -d && docker compose logs -f'
alias dprod='docker compose -f compose.yml -f compose.prod.yml up -d'
alias dtest='docker compose exec backend npm test && docker compose exec frontend npm test'
alias dclean='docker compose down -v && docker system prune -f'

# 디버깅
alias dlogs='docker compose logs -f --tail=100'
alias dshell-backend='docker compose exec backend sh'
alias dshell-frontend='docker compose exec frontend sh'
alias dmysql='docker compose exec database mysql -u todouser -ptodopassword123 todoapp'
```

---

## 💡 마무리

* ✅ 5-tier 아키텍처 (Nginx + React + Node.js + MySQL + Redis) 구축

* ✅ 서비스 간 통신과 데이터 흐름 설계 및 구현

* ✅ 개발과 운영 환경의 설정 분리

* ✅ 모니터링, 로깅, 헬스체크 시스템 구현