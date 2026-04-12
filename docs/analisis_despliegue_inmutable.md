# Análisis del Despliegue con Estrategia Inmutable

## Contexto

- **Fecha:** 11 de abril de 2026
- **Entorno:** Blacklist-env (AWS Elastic Beanstalk)
- **Estrategia aplicada:** Immutable
- **Herramienta de prueba:** Newman (Postman CLI) — 15 iteraciones, 8 segundos entre cada una

---

## Puntos Clave del Log de Newman

### 1. Zero Downtime confirmado

En las 15 iteraciones, el endpoint `GET /` (Health Check) retornó `200 OK` **sin excepción**.
Ningún request falló por indisponibilidad del servicio durante el despliegue.

Esto es la característica principal de la estrategia Immutable: las instancias antiguas
siguen atendiendo tráfico mientras las nuevas se aprovisionan en paralelo.

---

### 2. Cambio de versión visible en iteración 4

| Iteraciones | Comportamiento POST duplicado | Versión activa |
|-------------|------------------------------|----------------|
| 1 – 3       | Retorna `201 CREATED`        | Versión **anterior** (sin validación de duplicados) |
| **4 – 15**  | Retorna `400 BAD REQUEST`    | Versión **nueva** (con validación de duplicados) |

El cambio de comportamiento en la iteración 4 indica el momento exacto en que
Elastic Beanstalk transfirió el tráfico de las instancias viejas a las nuevas.

---

### 3. La transición fue instantánea y sin errores de red

Entre las iteraciones 3 y 4 no hubo:
- Timeouts
- Errores de conexión (connection refused)
- Respuestas 5xx

Esto confirma que el swap de instancias (característica de Immutable) se realizó
de forma atómica desde la perspectiva del cliente.

---

### 4. Los fallos de aserción son esperados y no indican problemas del servicio

Los fallos marcados en el log (ej: `Status 201 Created expected but got 400`) ocurrieron porque:

- El test "Agregar email" usa siempre `spam@example.com`
- A partir de la iteración 4, ese email ya existe en la BD y la nueva versión lo rechaza con 400
- Esto **no es un fallo del servicio**, sino evidencia de que la nueva lógica de negocio fue desplegada exitosamente

---

## Cómo Funciona la Estrategia Immutable

```
Estado inicial:
  [Instancia A - versión v1] ← recibe tráfico

Durante el despliegue:
  [Instancia A - versión v1] ← sigue recibiendo tráfico
  [Instancia B - versión v2] ← se aprovisiona (NO recibe tráfico aún)

Cuando B pasa health check:
  [Instancia A - versión v1] ← tráfico transferido a B
  [Instancia B - versión v2] ← AHORA recibe tráfico

Finalización:
  [Instancia A] ← eliminada
  [Instancia B - versión v2] ← único nodo activo
```

**Ventaja principal:** Si la versión nueva falla el health check, la instancia B es
eliminada y la instancia A nunca dejó de funcionar. Rollback instantáneo.

---

## Conclusión

La estrategia Immutable garantizó:
1. **Disponibilidad continua** durante el despliegue
2. **Transición limpia** entre versiones sin errores de red
3. **Rollback seguro** disponible en todo momento (las instancias viejas permanecen hasta confirmar salud de las nuevas)
