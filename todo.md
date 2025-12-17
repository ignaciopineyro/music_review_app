# Plan de Acción: Migración a Arquitectura de Microservicios Event-Driven

## 🎯 Objetivo
Transformar la aplicación monolítica actual en una arquitectura de microservicios con comunicación asíncrona mediante RabbitMQ.

## 📋 Análisis del Estado Actual
**Situación:** Aplicación monolítica FastAPI con endpoints de álbumes en un solo servicio
**Destino:** 2 microservicios independientes con bases de datos separadas

## 🏗️ Arquitectura Propuesta

```
┌─────────────────┐    ┌─────────────────┐
│  Auth Service   │    │ Reviews Service │
│  (Port 8001)    │    │  (Port 8002)    │
│                 │    │                 │
│ - JWT Auth      │    │ - Albums CRUD   │
│ - User Management│    │ - Reviews CRUD  │
│ - PostgreSQL DB1│    │ - PostgreSQL DB2│
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────┐    ┌──────────┘
                 │    │
         ┌───────▼────▼───────┐
         │     RabbitMQ       │
         │   Message Broker   │
         └────────────────────┘
```

## 📦 Reestructuración del Repositorio

### Estructura Propuesta:
```
music_review_app/
├── shared/                    # Código compartido
│   ├── __init__.py
│   ├── events.py             # Definiciones de eventos
│   ├── schemas.py            # Schemas compartidos
│   └── messaging.py          # Cliente RabbitMQ base
├── auth-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   └── jwt_service.py
│   │   ├── db.py
│   │   └── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/
├── reviews-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── album.py
│   │   │   └── review.py
│   │   ├── routers/
│   │   │   ├── albums.py      # Código actual migrado
│   │   │   └── reviews.py
│   │   ├── services/
│   │   │   └── auth_middleware.py
│   │   ├── db.py
│   │   └── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/
├── docker-compose.yml         # Orquestación completa
└── README.md
```

## 🔄 Plan de Implementación por Fases

### **Fase 1: Preparación del Entorno**
1. **Configurar RabbitMQ**
   - Agregar RabbitMQ al docker-compose.yml
   - Configurar exchanges, queues y routing keys

2. **Crear estructura de carpetas**
   - Reorganizar código existente
   - Crear directorios para cada microservicio

3. **Implementar código compartido**
   - Definir eventos (UserCreated, UserAuthenticated, etc.)
   - Cliente RabbitMQ base para publishing/consuming

### **Fase 2: Microservicio de Autenticación**
1. **Base del servicio**
   - FastAPI app independiente (puerto 8001)
   - Base de datos PostgreSQL separada
   - Modelos: User, RefreshToken

2. **Funcionalidades**
   - `/auth/register` - Registro de usuarios
   - `/auth/login` - Login con JWT
   - `/auth/refresh` - Refresh token
   - `/auth/verify` - Verificación de token

3. **Eventos salientes**
   - `UserRegistered` → Reviews Service
   - `UserAuthenticated` → Reviews Service
   - `TokenRevoked` → Reviews Service

### **Fase 3: Microservicio de Reviews**
1. **Migrar código actual**
   - Mover `albums.py` al reviews-service
   - Configurar base de datos independiente
   - Agregar modelo Review

2. **Middleware de autenticación**
   - Interceptar requests
   - Validar JWT localmente o via RabbitMQ
   - Cachear información de usuario

3. **Nuevos endpoints**
   - `/reviews/` - CRUD de reseñas
   - Vincular reseñas con álbumes y usuarios

4. **Eventos entrantes**
   - Escuchar `UserRegistered` para crear perfil local
   - Escuchar `TokenRevoked` para invalidar sesiones

### **Fase 4: Comunicación Event-Driven**
1. **Definir contratos de eventos**
   ```python
   # shared/events.py
   class UserRegisteredEvent:
       user_id: str
       email: str
       created_at: datetime
   
   class ReviewCreatedEvent:
       review_id: str
       user_id: str
       album_id: str
       rating: int
   ```

2. **Implementar publishers/consumers**
   - Auth service publica eventos de usuario
   - Reviews service consume eventos y publica reviews
   - Manejo de errores y retry logic

3. **Patrones de comunicación**
   - **Request/Reply**: Validación de tokens
   - **Publish/Subscribe**: Notificaciones de eventos
   - **Event Sourcing**: Auditoría de cambios

### **Fase 5: Orquestación con Docker**
1. **docker-compose.yml completo**
   ```yaml
   services:
     rabbitmq:
       image: rabbitmq:3-management
       ports: ["5672:5672", "15672:15672"]
     
     auth-db:
       image: postgres:15
       environment:
         POSTGRES_DB: auth_db
     
     reviews-db:
       image: postgres:15
       environment:
         POSTGRES_DB: reviews_db
     
     auth-service:
       build: ./auth-service
       ports: ["8001:8000"]
       depends_on: [auth-db, rabbitmq]
     
     reviews-service:
       build: ./reviews-service
       ports: ["8002:8000"]
       depends_on: [reviews-db, rabbitmq]
   ```

2. **Scripts de inicio**
   - `start-all.sh` - Todo el stack
   - `start-service.sh <service>` - Servicio específico

### **Fase 6: Testing y Validación**
1. **Tests de integración**
   - Flujos end-to-end
   - Comunicación entre servicios
   - Manejo de fallos

2. **Monitoreo**
   - Health checks para cada servicio
   - Métricas de RabbitMQ
   - Logs centralizados

## 🔧 Consideraciones Técnicas

### **Dependencias Adicionales**
- `aio-pika` o `celery` para RabbitMQ
- `python-jose` para JWT
- `passlib` para hashing de passwords
- `redis` (opcional) para caching

### **Configuración de Seguridad**
- JWT secrets independientes por servicio
- Validación de CORS entre servicios
- Rate limiting por servicio

### **Manejo de Datos**
- Migraciones independientes por servicio
- Consistencia eventual entre servicios
- Estrategias de backup separadas

## 🚀 Beneficios Esperados

1. **Escalabilidad:** Cada servicio escala independientemente
2. **Mantenibilidad:** Responsabilidades claras y separadas
3. **Resiliencia:** Fallo de un servicio no afecta al otro
4. **Flexibilidad:** Tecnologías diferentes por servicio si es necesario

## ⚠️ Desafíos a Considerar

1. **Complejidad:** Más componentes que monitorear
2. **Consistencia:** Manejo de transacciones distribuidas
3. **Debugging:** Trazabilidad entre servicios
4. **Latencia:** Comunicación asíncrona vs síncrona

## 📅 Timeline Estimado
- **Fase 1-2:** 1-2 semanas
- **Fase 3-4:** 2-3 semanas  
- **Fase 5-6:** 1 semana
- **Total:** 4-6 semanas

## ✅ Checklist de Implementación

### Fase 1 - Preparación
- [x] Agregar RabbitMQ a docker-compose.yml
- [x] Crear estructura de carpetas para microservicios
- [x] Implementar shared/messaging.py
- [x] Definir eventos en shared/events.py
- [x] Configurar dev-tools con virtualenv
- [x] Probar conectividad RabbitMQ

### Fase 2 - Auth Service
- [ ] Crear FastAPI app para autenticación
- [ ] Configurar base de datos PostgreSQL separada
- [ ] Implementar modelo User y RefreshToken
- [ ] Crear endpoints de autenticación (/register, /login, /refresh, /verify)
- [ ] Configurar publicación de eventos (UserRegistered, UserAuthenticated)

### Fase 3 - Reviews Service
- [ ] Migrar albums.py al reviews-service
- [ ] Configurar base de datos independiente
- [ ] Crear modelo Review
- [ ] Implementar middleware de autenticación
- [ ] Crear endpoints de reviews
- [ ] Configurar consumer de eventos de usuario

### Fase 4 - Comunicación Event-Driven
- [ ] Implementar publishers en auth-service
- [ ] Implementar consumers en reviews-service
- [ ] Configurar manejo de errores y retry logic
- [ ] Probar comunicación entre servicios

### Fase 5 - Docker & Orquestación
- [ ] Actualizar docker-compose.yml completo
- [ ] Crear Dockerfiles para cada servicio
- [ ] Crear scripts de inicio (start-all.sh, start-service.sh)
- [ ] Configurar variables de entorno

### Fase 6 - Testing
- [ ] Tests unitarios por servicio
- [ ] Tests de integración entre servicios
- [ ] Tests end-to-end
- [ ] Configurar health checks
- [ ] Implementar monitoreo y logs
