# CLAUDE.md - Instrucciones para Claude Code

## Contexto del Proyecto

Este es un proyecto del curso **Desarrollo de Software en la Nube (DevOps)** de la **Maestría en Ingeniería de Software (MISO)** de la **Universidad de los Andes**.

### Objetivo General
Desarrollar y desplegar un microservicio de **lista negra global de emails** sobre AWS Elastic Beanstalk (PaaS).

### Entregas del Proyecto (Incrementales)

El proyecto tiene múltiples entregas incrementales. Cada entrega construye sobre la anterior.

#### Entrega 1 (Actual): Despliegue Manual sobre PaaS
- **Funcionalidad:** API REST con 2 endpoints (POST y GET) para gestionar blacklist de emails
- **Infraestructura:** AWS Elastic Beanstalk + RDS PostgreSQL
- **Autenticación:** JWT Bearer Token (estático)
- **Documentación:** Postman + Documento de entrega con screenshots
- **Despliegue:** Manual (sin CI/CD)
- **Requerimiento especial:** Probar 4 estrategias de despliegue diferentes en EB

### Stack Tecnológico (Obligatorio)
- Python 3.8+
- Flask Framework
- Flask-SQLAlchemy
- Flask-RESTful
- Flask-Marshmallow
- Flask-JWT-Extended
- Werkzeug
- PostgreSQL
- Gunicorn (producción)

## Estructura del Proyecto

```
blacklist-project/
├── app/
│   ├── __init__.py          # App factory, DB, JWT, error handlers
│   ├── models.py            # Modelo BlacklistEntry (SQLAlchemy)
│   ├── resources.py         # Endpoints REST (Flask-RESTful)
│   └── schemas.py           # Validación con Marshmallow
├── tests/
│   ├── __init__.py
│   └── test_blacklist.py    # 17 tests (pytest)
├── .ebextensions/
│   └── 01_flask.config      # Config de Elastic Beanstalk
├── docs/
│   ├── Proyecto_1_entrega_1_Documento.md  # Template documento de entrega
│   ├── Blacklist_API_Postman_Collection.json
│   ├── GUIA_AWS_PASO_A_PASO.md
│   └── eb-strategies/       # Configs para 4 estrategias de despliegue
├── application.py           # Entry point (EB necesita este nombre)
├── requirements.txt
├── Procfile
├── deploy.sh                # Script auxiliar de despliegue
├── generate_token.py        # Utilidad para generar tokens JWT
├── .env.example
├── .gitignore
├── CLAUDE.md
└── README.md
```

## Endpoints de la API

| Método | Ruta                     | Auth    | Descripción                        |
|--------|--------------------------|---------|------------------------------------|
| GET    | `/`                      | No      | Health check para EB               |
| POST   | `/blacklists`            | Bearer  | Agregar email a lista negra        |
| GET    | `/blacklists/<email>`    | Bearer  | Consultar si email está bloqueado  |

### POST /blacklists
- **Body:** `{ email, app_uuid, blocked_reason? }`
- **Guarda internamente:** IP del request + timestamp
- **Response:** 201 con mensaje de confirmación

### GET /blacklists/<email>
- **Response:** `{ is_blacklisted: bool, blocked_reason: string|null }`

## Variables de Entorno

| Variable        | Descripción                | Default              |
|-----------------|----------------------------|----------------------|
| RDS_HOSTNAME    | Host de PostgreSQL         | localhost            |
| RDS_PORT        | Puerto de PostgreSQL       | 5432                 |
| RDS_DB_NAME     | Nombre de la BD            | blacklist_db         |
| RDS_USERNAME    | Usuario de la BD           | postgres             |
| RDS_PASSWORD    | Contraseña de la BD        | postgres             |
| JWT_SECRET_KEY  | Clave secreta para JWT     | super-secret-key-... |

## Comandos Útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar localmente
python application.py

# Generar token JWT de prueba
python generate_token.py

# Ejecutar con gunicorn (producción)
gunicorn --bind :5000 application:application
```

## Reglas para futuras entregas

- El código debe mantenerse limpio y bien documentado
- Cada entrega incrementa funcionalidad sobre la anterior
- Respetar el contrato de la API (endpoints definidos)
- Los tests deben crearse y mantenerse
- El documento de entrega es obligatorio y tiene formato específico
