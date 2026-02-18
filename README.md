# Calculadora de ingredientes para obrador de heladería

Aplicación web en Python para gestionar recetas de helado y calcular cantidades de ingredientes en función de los kilos a producir.

## Funcionalidades

- Crear y borrar ingredientes desde la pestaña **Ingredientes**.
- Listar ingredientes con orden A-Z / Z-A y ver en qué recetas se usan.
- Crear recetas seleccionando ingredientes desde un desplegable (usa ingredientes previamente cargados).
- Guardar observaciones por receta.
- Calcular automáticamente gramos por ingrediente para cualquier cantidad en kg.
- Interfaz estilo tablet inspirada en tus bocetos.

---

## Guía para principiantes (Windows, paso a paso)

> Si no sabes nada de programación, sigue estos pasos exactamente en orden.

### 1) Instalar Python (solo la primera vez)

1. Ve a: https://www.python.org/downloads/windows/
2. Descarga **Python 3**.
3. Durante instalación, marca la casilla **Add Python to PATH**.
4. Pulsa **Install Now**.

### 2) Abrir la carpeta del proyecto

1. Abre el Explorador de archivos.
2. Entra en la carpeta donde tengas el repo (por ejemplo: `C:\Users\julia\OneDrive\Escritorio\Calculadora-obrador`).
3. Comprueba que dentro existan archivos como `app.py`, `README.md`, carpetas `static`, `templates`.

### 3) Abrir la terminal en esa carpeta

Tienes 2 opciones:

- Opción A: en la barra de ruta del Explorador escribe `powershell` y pulsa Enter.
- Opción B: clic derecho dentro de la carpeta → **Abrir en Terminal**.

### 4) Verificar Python

En la terminal, ejecuta:

```powershell
py --version
```

Si no funciona, prueba:

```powershell
python --version
```

Si ambos fallan, Python no está instalado correctamente (vuelve al paso 1).

### 5) Iniciar la app

Dentro de la carpeta del proyecto, ejecuta:

```powershell
py app.py
```

Si `py` falla, usa:

```powershell
python app.py
```

Cuando arranca bien, la terminal se queda abierta y el servidor escucha en el puerto `5000`.

### 6) Abrir en el navegador del ordenador

Abre Chrome/Edge/Firefox y entra a:

```text
http://localhost:5000
```

Si carga la web, la app ya está funcionando.

### 7) Abrir en tablet/móvil (misma WiFi)

1. En la terminal del ordenador, ejecuta:

```powershell
ipconfig
```

2. Busca la línea **Dirección IPv4** (algo como `192.168.1.34`).
3. En la tablet abre:

```text
http://192.168.1.34:5000
```

> Cambia la IP por la tuya real.

### 8) Flujo de prueba recomendado

1. Ir a **Ingredientes**.
2. Crear 2 o 3 ingredientes.
3. Ir a **Crear receta** y seleccionar esos ingredientes en el desplegable.
4. Guardar receta.
5. Ir a **Elaborar**, elegir receta, poner kilos, pulsar **Calcular**.

### 9) Parar el servidor

En la terminal donde corre la app, pulsa:

- `Ctrl + C`

---


## Si solo ves `.gitkeep` (solución rápida)

Si en tu PC y en GitHub solo aparece `.gitkeep`, significa que el código de la app **todavía no fue subido** al remoto.

Haz esto en PowerShell, en tu carpeta del repo:

```powershell
cd C:\Users\julia\OneDrive\Escritorio\Calculadora-obrador
git fetch --all --prune
git pull origin main
dir
```

- Si después de eso siguen sin aparecer `app.py`, `README.md`, `static`, `templates`, entonces en GitHub aún no está publicado el código.
- En ese caso, opción fácil para empezar hoy: en GitHub crea los archivos (`app.py`, `templates/index.html`, `static/app.js`, `static/styles.css`) y súbelos desde la web, o usa GitHub Desktop para sincronizar sin comandos complejos.

> Resumen corto: **los archivos no están en tu PC porque todavía no están en tu GitHub remoto**.

---

## Problemas frecuentes (y solución rápida)

### "No abre localhost:5000"

- Revisa que la terminal siga abierta con `py app.py` ejecutándose.
- Revisa que estás en la carpeta correcta (donde está `app.py`).

### "En la tablet no abre"

- Ordenador y tablet deben estar en la misma WiFi.
- Usa `http://IP_DEL_ORDENADOR:5000` (no `localhost` en la tablet).
- Si hay firewall de Windows, permite el acceso para Python en red privada.

### "La terminal dice que no reconoce py/python"

- Python no está instalado o no quedó en PATH.
- Reinstala Python y marca **Add Python to PATH**.

---

## Ejecutar tests

```bash
python -m unittest discover -s tests
```
