# webhookpolicuyo
Webhook de búsqueda en listado de precios

# 🛠️ Cotizador de Productos para Ferretería

Este proyecto es una API web desarrollada con **Flask** que permite buscar y cotizar productos a partir de un archivo CSV utilizando coincidencia de texto difusa con **RapidFuzz**.

Ideal para integrarse con chatbots u otros sistemas que necesiten sugerencias inteligentes de productos por nombre o segmento.

---

## 🚀 Endpoints disponibles

| Método | Ruta              | Descripción                                                                 |
|--------|-------------------|-----------------------------------------------------------------------------|
| GET    | `/`               | Health check (respuesta básica para confirmar que la API está activa).     |
| GET    | `/segmentos`      | Devuelve todos los segmentos disponibles y la cantidad de productos por cada uno. |
| POST   | `/cotizar`        | Recibe una o más consultas de productos y devuelve coincidencias.          |

---

## 🧠 Funcionalidades

- 🔍 Búsqueda inteligente con coincidencia parcial de texto (`partial_ratio` de RapidFuzz).
- 🗂️ Filtrado opcional por segmento (`SEGMENTO` del CSV).
- 📊 Devolución de resultados con puntaje de coincidencia.
- 🧵 Soporte para múltiples consultas en una sola petición.
- 🐛 Manejo de errores detallado para entradas inválidas.

---

## 🗂️ Estructura de archivos

```
├── app.py               # Código principal del servidor Flask
├── main.py              # Punto de entrada que inicia el servidor
├── listado.csv          # Catálogo de productos con columnas: Descripcion, Precio Contado, Precio Tarjeta, SEGMENTO
├── requirements.txt     # Dependencias para ejecutar localmente o desplegar
├── pyproject.toml       # Configuración de dependencias alternativa
```

---

## ▶️ Cómo correrlo localmente

### 1. Clonar el repositorio

```bash
git clone https://github.com/santiruss28/cotizador-ferreteria.git
cd cotizador-ferreteria
```

### 2. Instalar dependencias

#### Opción A - Usando `requirements.txt`
```bash
pip install -r requirements.txt
```

#### Opción B - Usando `pyproject.toml`
```bash
pip install .
```

### 3. Iniciar el servidor Flask

```bash
python main.py
```

El servidor estará corriendo en `http://localhost:3000`.

---

## 🌐 Despliegue en Render

1. Crear una cuenta en [https://render.com](https://render.com)
2. Clic en **"New Web Service"**
3. Conectar tu repositorio de GitHub
4. Completar la configuración:

| Campo            | Valor                                      |
|------------------|--------------------------------------------|
| Build Command    | `pip install -r requirements.txt`          |
| Start Command    | `gunicorn -w 1 -b 0.0.0.0:3000 main:app`    |
| Instance Type    | `Free`                                     |
| Root Directory   | (dejar vacío)                              |

> ⚠️ Asegurate de incluir el archivo `listado.csv` en tu repositorio.

---

## 📫 Ejemplo de consulta POST

### Consulta simple

```bash
curl -X POST https://tu-api.onrender.com/cotizar \
-H "Content-Type: application/json" \
-d '{"consulta": "rosca gas", "segmento": "GAS"}'
```

### Consulta múltiple

```bash
curl -X POST https://tu-api.onrender.com/cotizar \
-H "Content-Type: application/json" \
-d '{
  "consultas": [
    {"consulta": "rosca gas", "segmento": "GAS"},
    {"consulta": "válvula doble"}
  ]
}'
```

---

## 🧩 Requisitos

- Python 3.10+
- Flask
- Pandas
- RapidFuzz
- Gunicorn (para producción)

---

## 📄 Licencia

Este proyecto se publica bajo licencia MIT.
