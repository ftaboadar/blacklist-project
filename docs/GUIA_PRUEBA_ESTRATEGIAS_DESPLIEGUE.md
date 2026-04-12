# Guía: Cómo Probar las Estrategias de Despliegue con Newman

## Qué vas a demostrar

Que el servicio **sigue respondiendo** mientras Elastic Beanstalk despliega una nueva versión.
Newman corre en paralelo al deploy y registra cada request — si hay downtime, aparecerá un error de conexión en el log.

---

## Requisitos previos

- Entorno EB funcionando (Health: OK)
- Node.js instalado (`node --version`)
- Python con el venv del proyecto activado
- AWS CLI configurado

---

## Paso 1 — Instalar Newman

```bash
npm install -g newman
# Si no queda en el PATH, usar npx newman en lugar de newman
```

---

## Paso 2 — Obtener la URL de tu entorno EB

```bash
aws elasticbeanstalk describe-environments \
  --environment-names <NOMBRE_DE_TU_ENTORNO> \
  --region us-east-1 \
  --query "Environments[0].CNAME" \
  --output text
```

> En Windows PowerShell reemplazar `\` por `` ` ``

---

## Paso 3 — Generar el token JWT

```bash
# Activar el entorno virtual
source venv/bin/activate          # Linux/Mac
# .venv\Scripts\Activate.ps1     # Windows PowerShell

# Setear el mismo JWT_SECRET_KEY que tiene tu entorno EB
export JWT_SECRET_KEY="<tu-jwt-secret-key>"        # Linux/Mac
# $env:JWT_SECRET_KEY="<tu-jwt-secret-key>"        # Windows PowerShell

python generate_token.py
# Copia el token que aparece
```

> El token expira en 15 minutos. Si expira, genera uno nuevo.

---

## Paso 4 — Configurar la estrategia en EB Console

1. Ve a **EB Console → tu entorno → Configuration**
2. Sección **Rolling updates and deployments**
3. Cambia **Deployment policy** a la estrategia que quieras probar:

| Estrategia | Comportamiento esperado durante el test |
|------------|----------------------------------------|
| `All at once` | Puede haber requests fallidos (downtime breve) |
| `Rolling` | Capacidad reducida temporalmente, sin caída total |
| `Rolling with additional batch` | Sin caída, capacidad completa en todo momento |
| `Immutable` | Sin caída, swap atómico entre versiones |

4. Guarda los cambios (esto NO despliega nada aún)

---

## Paso 5 — Preparar el ZIP con algún cambio mínimo

Necesitas subir una nueva versión para que EB ejecute el despliegue.
Puedes agregar un comentario en `application.py` como cambio mínimo:

```bash
# Linux/Mac
zip -r deploy-v2.zip application.py requirements.txt Procfile app/ .ebextensions/

# Windows PowerShell
Compress-Archive -Path application.py, requirements.txt, Procfile, app, .ebextensions `
  -DestinationPath deploy-v2.zip -Force
```

---

## Paso 6 — Correr Newman en loop Y subir el ZIP al mismo tiempo

### Ventana 1: iniciar Newman ANTES de subir el ZIP

```bash
# Linux/Mac
newman run docs/Blacklist_API_Postman_Collection.json \
  --env-var "base_url=http://<TU_URL_EB>" \
  --env-var "token=<TU_TOKEN>" \
  --iteration-count 20 \
  --delay-request 8000

# Windows PowerShell
npx newman run docs/Blacklist_API_Postman_Collection.json `
  --env-var "base_url=http://<TU_URL_EB>" `
  --env-var "token=<TU_TOKEN>" `
  --iteration-count 20 `
  --delay-request 8000
```

`--iteration-count 20` con `--delay-request 8000` (8 seg) = ~160 segundos de pruebas.
Suficiente para cubrir cualquier estrategia de despliegue.

### Ventana 2: subir el ZIP mientras Newman corre

En **EB Console → Upload and deploy → subir deploy-v2.zip**

---

## Paso 7 — Interpretar los resultados

### Señales de zero downtime (estrategias Rolling / Immutable)
```
→ Health Check
  GET http://... [200 OK, ...]
  √  Status 200
  √  Service healthy
```
Todas las iteraciones responden 200 — el servicio nunca estuvo caído.

### Señal de downtime (estrategia All at once)
```
→ Health Check
  GET http://... [error] connect ECONNREFUSED
  1. Status 200   ← fallo por conexión rechazada
```
Aparecen errores de conexión durante las iteraciones del deploy.

### Señal de que la nueva versión fue desplegada
Busca un cambio de comportamiento entre iteraciones — por ejemplo un endpoint
que antes retornaba 201 y ahora retorna 400, o un campo nuevo en la respuesta.
Ese es el momento exacto del swap.

---

## Paso 8 — Guardar la evidencia

```bash
# Guardar el output de Newman en un archivo
npx newman run docs/Blacklist_API_Postman_Collection.json \
  --env-var "base_url=http://<TU_URL_EB>" \
  --env-var "token=<TU_TOKEN>" \
  --iteration-count 20 \
  --delay-request 8000 \
  --reporters cli,json \
  --reporter-json-export docs/resultado_newman_<estrategia>.json
```

Tomar screenshots de:
1. Configuración con la estrategia activa
2. Dashboard EB durante el deploy (instancias en transición)
3. Terminal con Newman corriendo
4. Estado final: Health OK

---

## Resumen por estrategia

| Estrategia | Requiere Load Balanced | Downtime esperado | Velocidad |
|------------|----------------------|-------------------|-----------|
| All at once | No | Sí (breve) | Más rápido |
| Rolling | Sí | No (capacidad reducida) | Medio |
| Rolling with additional batch | Sí | No (capacidad completa) | Medio |
| Immutable | Sí | No (swap atómico) | Más lento |
