# Guía de Despliegue Manual - Entrega 1

## Requisitos previos

- Cuenta AWS activa con permisos para EB + RDS
- AWS CLI instalado y configurado (`aws configure`)
- Python 3.8+ instalado localmente
- `pip` actualizado

---

## Paso 1 — Preparar el entorno local

```bash
# Clonar o descargar el proyecto
cd blacklist-project

# Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar y editar variables de entorno locales
cp .env.example .env
# Editar .env con tus valores locales
```

---

## Paso 2 — Verificar que los tests pasan

```bash
python -m pytest tests/ -v
# Deben pasar los 17 tests
```

---

## Paso 3 — Crear la base de datos RDS PostgreSQL

1. Ve a **AWS Console → RDS → Create database**
2. Configuración:
   - Engine: **PostgreSQL**
   - Template: **Free tier**
   - DB identifier: `blacklist-db`
   - Username: `postgres`
   - Password: (anota esta contraseña)
   - DB name: `blacklist_db`
   - Public access: **Yes** (solo para pruebas, en prod: No)
3. En **Security Group**, agregar inbound rule:
   - Type: PostgreSQL, Port: 5432, Source: `0.0.0.0/0` (para pruebas)
4. Esperar ~5 min a que el estado sea **Available**
5. Copiar el **Endpoint** (hostname) para el siguiente paso

---

## Paso 4 — Crear la aplicación en Elastic Beanstalk

### 4.1 Crear el ZIP de despliegue

Incluir en el ZIP (desde la raíz del proyecto):
```
application.py
requirements.txt
Procfile
app/
.ebextensions/
```

```bash
# En Linux/Mac
zip -r blacklist-app.zip application.py requirements.txt Procfile app/ .ebextensions/

# En Windows (PowerShell)
Compress-Archive -Path application.py, requirements.txt, Procfile, app, .ebextensions -DestinationPath blacklist-app.zip
```

> **Importante:** NO incluir `venv/`, `.env`, ni `tests/` en el ZIP.

### 4.2 Crear el entorno en EB Console

1. Ve a **AWS Console → Elastic Beanstalk → Create application**
2. Application name: `blacklist-api`
3. Platform: **Python** → Python 3.8
4. Application code: subir el ZIP creado
5. Click **Configure more options** (antes de crear)

### 4.3 Configurar variables de entorno en EB

En **Configure more options → Software → Environment properties**, agregar:

| Key           | Value                          |
|---------------|--------------------------------|
| RDS_HOSTNAME  | (endpoint de tu RDS)           |
| RDS_PORT      | 5432                           |
| RDS_DB_NAME   | blacklist_db                   |
| RDS_USERNAME  | postgres                       |
| RDS_PASSWORD  | (tu contraseña de RDS)         |
| JWT_SECRET_KEY| super-secret-key-devops-2024   |

6. Click **Create environment** y esperar ~5 min

---

## Paso 5 — Verificar el despliegue

```bash
# Health check (reemplaza la URL con la de tu entorno EB)
curl https://blacklist-api.us-east-1.elasticbeanstalk.com/

# Respuesta esperada:
# {"status": "healthy", "service": "blacklist-api"}
```

---

## Paso 6 — Generar token JWT para pruebas

```bash
# Opción 1: desde el proyecto local
python generate_token.py

# Opción 2: manual con Python
python -c "
from app import create_app
from flask_jwt_extended import create_access_token
app = create_app()
with app.app_context():
    print(create_access_token(identity='test'))
"
```

---

## Paso 7 — Probar los endpoints

### POST /blacklists — Agregar email

```bash
curl -X POST https://<tu-url-eb>/blacklists \
  -H "Authorization: Bearer <tu-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "spam@example.com", "app_uuid": "uuid-app-1", "blocked_reason": "Spam"}'

# Respuesta esperada (201):
# {"message": "Email 'spam@example.com' has been added to the global blacklist successfully."}
```

### GET /blacklists/<email> — Consultar email

```bash
curl https://<tu-url-eb>/blacklists/spam@example.com \
  -H "Authorization: Bearer <tu-token>"

# Respuesta esperada (200):
# {"is_blacklisted": true, "blocked_reason": "Spam"}
```

---

## Paso 8 — Probar las 4 estrategias de despliegue

Para cada estrategia, debes:
1. Tomar un **screenshot** del dashboard de EB durante el despliegue
2. Tomar un **screenshot** del estado final (Health: OK)

### Cómo cambiar la estrategia desde la consola

1. Ve a tu entorno en EB → **Configuration**
2. Sección **Rolling updates and deployments**
3. Cambia **Deployment policy** y guarda

### Estrategia 1: All at Once

- En consola: Deployment policy = `All at once`
- Archivo de referencia: `docs/eb-strategies/01_all_at_once.config`
- Característica: Despliega en TODAS las instancias simultáneamente. Causa downtime breve.

### Estrategia 2: Rolling

- En consola: Deployment policy = `Rolling`
- Archivo de referencia: `docs/eb-strategies/02_rolling.config`
- Característica: Despliega por lotes. Reduce capacidad temporalmente, sin downtime total.

### Estrategia 3: Rolling with Additional Batch

- En consola: Deployment policy = `Rolling with additional batch`
- Archivo de referencia: `docs/eb-strategies/03_rolling_additional_batch.config`
- Característica: Agrega instancias extras antes de retirar las viejas. Mantiene capacidad completa.

### Estrategia 4: Immutable

- En consola: Deployment policy = `Immutable`
- Archivo de referencia: `docs/eb-strategies/04_immutable.config`
- Característica: Crea instancias nuevas completamente. La más segura, posibilidad de rollback inmediato.

---

## Troubleshooting común

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| 502 Bad Gateway | App no arranca | Ver logs en EB → Logs → Last 100 lines |
| Cannot connect to DB | Security Group de RDS | Agregar inbound rule para el SG del EB |
| ModuleNotFoundError | Dependencia faltante | Verificar `requirements.txt` en el ZIP |
| 401 en endpoints | Token incorrecto | Regenerar token con `generate_token.py` |

### Ver logs en EB Console

1. Ve a tu entorno → **Logs**
2. Click **Request Logs → Last 100 lines**
3. Busca errores en `/var/log/web.stdout.log`

---

## Limpieza (después de la entrega)

> Para evitar costos, elimina los recursos al terminar:

1. **EB**: Environments → Terminate environment
2. **RDS**: Databases → Delete (desmarcar "Create final snapshot" para free tier)
