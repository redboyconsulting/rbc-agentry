## Instalación

### Preparación de Ollama

#### 1. Instalar e iniciar el servidor

Para la opción nativa en Windows, si todavía no tienes Ollama instalado:

```powershell
winget install --exact --id Ollama.Ollama
```

Abre una terminal nueva después de instalarlo. Si la aplicación Ollama no
está ejecutándose, inicia el servidor en esa terminal y déjala abierta:

```powershell
ollama serve
```

Si Ollama ya está iniciado, no ejecutes otro `ollama serve`: ambos intentarían
usar el puerto `11434`. Para la opción Docker, crea el contenedor con el
comando de la sección anterior o ejecuta `docker start ollama` si ya existe
y está detenido. Usa solo una opción, nativa o Docker, a la vez.

#### 2. Elegir el modelo

El agente básico activa el **razonamiento** automáticamente si el modelo lo
soporta: el modelo piensa antes de responder, lo que mejora mucho las
respuestas a preguntas complejas a cambio de tardar más. Todos los modelos de
esta tabla soportan herramientas (tools), que el agente necesita.

| Modelo | Descarga | Razonamiento | Recomendado para |
|---|---|---|---|
| `qwen3:14b` | ~9.3 GB | Sí | **Recomendado.** GPU con 12 GB+ de VRAM o 16 GB+ de RAM |
| `qwen3:8b` | ~5.2 GB | Sí | GPU con 8 GB de VRAM o 16 GB de RAM |
| `qwen3:4b` | ~2.5 GB | Sí | Equipos modestos; respuestas más simples |
| `llama3.2` | ~2.0 GB | No | Pruebas rápidas; respuestas básicas |

Sin GPU dedicada el modelo corre en CPU y responde más despacio, sobre todo
con razonamiento. Para comprobar si un modelo descargado soporta razonamiento,
ejecuta `ollama show MODELO` y revisa que en `Capabilities` aparezca `thinking`.

#### 3. Descargar y probar el modelo

En **otra terminal de PowerShell**, con el servidor iniciado, ejecuta:

```powershell
ollama list
ollama pull qwen3:14b
ollama show qwen3:14b
ollama run qwen3:14b "Responde en español: ¿estás listo para trabajar?"
Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
```

`pull` descarga el modelo; `show` muestra sus capacidades (`thinking` indica
razonamiento); `run` lo carga y ejecuta una pregunta de prueba, mostrando
primero el razonamiento (`Thinking...`) y después la respuesta. Con una
pregunta en el comando, la prueba termina después de responder.
La consulta a `/api/tags` comprueba el servidor y lista los modelos, pero no
ejecuta inferencia. Si algún comando falla, resuelve el error antes de seguir.

#### 4. Instalar Python, preparar y activar el entorno virtual

El proyecto requiere Python 3.10 o superior. Para estos pasos usa **Python
3.12**. Si no lo tienes instalado, descárgalo e instálalo desde PowerShell:

```powershell
winget install --exact --id Python.Python.3.12
```

Abre una terminal nueva después de instalarlo y comprueba la versión:

```powershell
py -3.12 --version
```

Desde la raíz del repositorio, crea el entorno virtual `.venv` y actívalo.
Si ya existe un entorno válido con Python 3.12, reutilízalo sin crearlo de nuevo:

```powershell
cd "C:\Users\User\OneDrive\Desktop\agent-framework"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea `Activate.ps1` por la política de ejecución, permite
scripts solo en esta sesión y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Con el entorno activo, instala los paquetes del repositorio y la dependencia
MCP que necesita Playwright:

```powershell
python -m pip install --upgrade pip
python -m pip install -e .\python\packages\core -e .\python\packages\ollama "mcp>=1.27.0,<2"
python -m pip check
python -c "import sys; print(sys.executable); from agent_framework import Agent, MCPStdioTool; from agent_framework.ollama import OllamaChatClient; print('Importaciones correctas')"
```

La ruta impresa debe terminar en `.venv\Scripts\python.exe`. Si algún comando
falla, resuelve el error antes de continuar.

El paso 5 también activa Playwright en modo offline. Necesitas **Node.js,
npx y Microsoft Edge**. Si no tienes Node.js, instálalo:

```powershell
winget install --exact --id OpenJS.NodeJS.LTS
```

Si acabas de instalar Node.js, abre una terminal nueva, vuelve a la raíz del
repositorio y activa otra vez `.\.venv\Scripts\Activate.ps1`. Después verifica
Node.js y prepara el paquete MCP en la cache de npm una vez, con internet:

```powershell
node --version
npx --version
npx -y @playwright/mcp@latest --help
```

Continúa con el paso 5 en esta misma terminal. En cada terminal nueva debes
activar el entorno de nuevo; `deactivate` lo desactiva.

#### 5. Prueba el template

```powershell
cd "C:\Users\User\OneDrive\Desktop\agent-framework"
$env:OLLAMA_MODEL = "qwen3:14b"
$env:ENABLE_PLAYWRIGHT_MCP = "1"
$env:PLAYWRIGHT_MCP_OFFLINE = "1"
$env:PLAYWRIGHT_BROWSER = "msedge"
python .\python\samples\02-agents\providers\ollama\ollama_agent_basic.py
```

Si Playwright MCP termina con `TimeoutError`, prepara su paquete una vez:

```powershell
npx -y @playwright/mcp@latest --help
```

Luego reinicia el agente usando la cache de npm y Microsoft Edge:

```powershell
$env:ENABLE_PLAYWRIGHT_MCP = "1"
$env:PLAYWRIGHT_MCP_OFFLINE = "1"
$env:PLAYWRIGHT_BROWSER = "msedge"
python .\python\samples\02-agents\providers\ollama\ollama_agent_basic.py
```

Este modo evita consultas al registro de npm durante el arranque; no impide
que el navegador visite sitios web. Requiere Node.js, el paquete en cache y
Edge instalado. Comprueba que aparezca `Playwright MCP conectado` y pide
`Abre https://example.com`. Si falla la conexion, el agente sigue sin navegador.
Para volver al arranque normal, elimina `PLAYWRIGHT_MCP_OFFLINE` de la terminal
con `Remove-Item Env:\PLAYWRIGHT_MCP_OFFLINE`.

## Lista de Agentes Disponibles

#### Agente básico interactivo con razonamiento

Este ejemplo conversa por consola y responde en streaming. Escribe `salir`
para terminar.

```powershell
$env:OLLAMA_MODEL = "qwen3:14b"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_agent_basic.py"
```

Al iniciar, el agente indica el modelo y si el razonamiento quedó activado,
por ejemplo `Modelo: qwen3:14b | Razonamiento: activado`. En cada pregunta
muestra primero `Razonamiento:` (lo que el modelo piensa) y luego `Agent:`
(la respuesta final). Con un modelo sin razonamiento, como `llama3.2`, el
agente funciona igual, pero sin esa fase y con respuestas más básicas.

Puedes ajustar el razonamiento con estas variables de entorno:

| Variable | Valor | Efecto |
|---|---|---|
| `OLLAMA_THINK` | `0` | Desactiva el razonamiento aunque el modelo lo soporte (respuestas más rápidas) |
| `OLLAMA_SHOW_REASONING` | `0` | Mantiene el razonamiento, pero solo muestra la respuesta final |

```powershell
# Ejemplo: razonar sin mostrar el razonamiento en consola
$env:OLLAMA_SHOW_REASONING = "0"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_agent_basic.py"
Remove-Item Env:OLLAMA_SHOW_REASONING
```

Para habilitar las herramientas de navegador del agente básico, necesitas
**Node.js y npx** en el PATH y conexión a internet para descargar el servidor
MCP la primera vez. Las acciones del navegador no requieren aprobación en
este ejemplo; habilítalas solo para tareas y sitios de confianza.

```powershell
$env:ENABLE_PLAYWRIGHT_MCP = "1"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_agent_basic.py"
$env:ENABLE_PLAYWRIGHT_MCP = "0"
```

#### Cliente Ollama directo con herramientas

```powershell
$env:OLLAMA_MODEL = "qwen3:14b"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_chat_client.py"
```

#### Agente con razonamiento

Ejemplo mínimo que hace una sola pregunta e imprime por separado el
razonamiento y la respuesta. Necesita un modelo con razonamiento, como
`qwen3:14b` o `qwen3:8b`.

```powershell
$env:OLLAMA_MODEL = "qwen3:14b"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_agent_reasoning.py"
```

#### Cliente multimodal con imagen

Necesita un modelo con soporte de imágenes; el ejemplo genera su propia
imagen de prueba.

```powershell
ollama pull gemma3:4b
$env:OLLAMA_MODEL = "gemma3:4b"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_chat_multimodal.py"
```

#### Ollama mediante el cliente compatible con OpenAI

En este ejemplo, `OLLAMA_ENDPOINT` debe incluir **`/v1/`**. El código usa una
clave de API de relleno; no necesitas una cuenta ni una clave de OpenAI.

```powershell
$env:OLLAMA_ENDPOINT = "http://localhost:11434/v1/"
$env:OLLAMA_MODEL = "qwen3:14b"
& "$repo\.venv\Scripts\python.exe" "$repo\python\samples\02-agents\providers\ollama\ollama_with_openai_chat_client.py"
```
