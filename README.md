# EVE-Mouse — Documentação Técnica do Projeto

> Controle mouse e teclado do seu Linux pelo celular via rede local (Wi-Fi), usando apenas o browser.  
> Compatível com **X11 e Wayland** (Fedora 44 / GNOME).

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Stack Técnica](#stack-técnica)
4. [Estrutura de Pastas](#estrutura-de-pastas)
5. [Módulos](#módulos)
   - [GUI (Janela de Configuração)](#módulo-1--gui-janela-de-configuração)
   - [Servidor Web](#módulo-2--servidor-web-fastapi)
   - [Injeção de Input](#módulo-3--injeção-de-input)
   - [Frontend Mobile](#módulo-4--frontend-mobile)
   - [Autenticação](#módulo-5--autenticação)
   - [Configuração](#módulo-6--configuração)
6. [Protocolo WebSocket](#protocolo-websocket)
7. [Instalação e Dependências](#instalação-e-dependências)
8. [Fluxo de Execução](#fluxo-de-execução)
9. [Pontos de Atenção](#pontos-de-atenção)

---

## Visão Geral

O EVE-Mouse é um aplicativo para **Linux (Fedora 44 / GNOME)** composto por duas partes:

- **App desktop (GTK4):** uma janelinha de configuração que sobe um servidor web local.
- **Frontend mobile:** uma página web acessada pelo browser do celular (iPhone ou Android), que transforma a tela inteira em um **trackpad + campo de teclado**.

A comunicação entre celular e PC acontece via **WebSocket** pela rede local (Wi-Fi), com latência mínima. Toda injeção de mouse e teclado é feita via `/dev/uinput` — camada do kernel Linux que funciona tanto com X11 quanto com Wayland.

---

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│                  PC LINUX (Fedora 44)            │
│                                                  │
│  ┌─────────────────┐     ┌────────────────────┐  │
│  │  GUI GTK4       │────▶│  FastAPI + WS      │  │
│  │  (configuração) │     │  porta :1010       │  │
│  └─────────────────┘     └────────┬───────────┘  │
│                                   │              │
│                       ┌───────────▼───────────┐  │
│                       │   input_controller    │  │
│                       │   python-evdev        │  │
│                       │   /dev/uinput         │  │
│                       │   ydotool (texto)     │  │
│                       └───────────────────────┘  │
└──────────────────────────────────────────────────┘
                ▲
                │  WebSocket — rede local Wi-Fi
                │  http://192.168.x.x:1010
                ▼
┌──────────────────────────┐
│  iPhone / Android        │
│  (Safari ou Chrome)      │
│                          │
│  ┌──────────────────┐    │
│  │ Campo de texto   │    │
│  ├──────────────────┤    │
│  │                  │    │
│  │  Área Trackpad   │    │
│  │  (touch & drag)  │    │
│  │                  │    │
│  ├─────────┬────────┤    │
│  │  [  L ] │ [  R ] │    │
│  └─────────┴────────┘    │
└──────────────────────────┘
```

---

## Stack Técnica

| Camada | Tecnologia | Motivo |
|---|---|---|
| GUI Linux | Python + PyGObject (GTK4) | Nativo GNOME, sem dependências pesadas |
| Servidor web | FastAPI (Python) | Async nativo, suporte a WebSocket |
| Injeção de input | python-evdev + /dev/uinput | Única opção confiável no Wayland |
| Digitação de texto | ydotool | Lida com mapeamento de caracteres automaticamente |
| Frontend mobile | HTML + CSS + JS vanilla | Sem framework, leve, funciona em qualquer browser |
| Comunicação | WebSocket (via FastAPI) | Latência mínima para trackpad em tempo real |
| Autenticação | bcrypt + token UUID4 em cookie | Seguro para uso em rede local |
| Config persistida | JSON em `~/.config/EVE-Mouse/config.json` | Simples, sem banco de dados |

---

## Estrutura de Pastas

```
EVE-Mouse/
├── main.py                   # Entrypoint: inicia GUI e servidor em paralelo
├── requirements.txt          # Dependências Python
├── EVE-Mouse.desktop         # Atalho para o menu do GNOME
│
└── app/
    ├── __init__.py
    ├── gui.py                # Janela GTK4 com configurações
    ├── server.py             # FastAPI: rotas HTTP + WebSocket
    ├── input_controller.py   # Injeção de mouse/teclado via evdev + ydotool
    ├── auth.py               # Login com bcrypt e gerenciamento de sessões
    ├── config.py             # Leitura e escrita do config.json
    │
    └── static/
        ├── login.html        # Tela de login exibida no browser do celular
        └── index.html        # Interface trackpad + campo de texto
```

---

## Módulos

### Módulo 1 — GUI (Janela de Configuração)

**Arquivo:** `app/gui.py`  
**Tecnologia:** Python + PyGObject (GTK4)

A janela é simples e minimalista. Deve conter:

| Elemento | Tipo | Função |
|---|---|---|
| Manter em segundo plano | Switch | Mantém o servidor rodando mesmo após fechar a janela |
| Sessão única | Switch | Gera um token novo a cada abertura; ao fechar, o token expira |
| Expiração da sessão | Campo de texto | Tempo em minutos; `0` = sem limite |
| Senha de acesso | Campo senha | A mesma senha que será usada no login do browser |
| URL atual | Label (somente leitura) | Exibe `http://192.168.x.x:1010` automaticamente |
| Copiar URL | Botão | Copia a URL para a área de transferência |
| Iniciar / Parar | Botão | Liga ou desliga o servidor web |

**Detecção automática do IP local:**

```python
import socket

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
```

---

### Módulo 2 — Servidor Web (FastAPI)

**Arquivo:** `app/server.py`  
**Tecnologia:** FastAPI + Uvicorn

#### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Serve o `index.html` (trackpad); redireciona para `/login` se não autenticado |
| `GET` | `/login` | Serve o `login.html` |
| `POST` | `/auth/login` | Recebe `{ "password": "..." }`, valida, retorna cookie de sessão |
| `GET` | `/auth/logout` | Invalida o cookie de sessão |
| `WS` | `/ws` | WebSocket principal; verifica cookie antes de aceitar |
| `GET` | `/status` | Healthcheck — retorna `{ "ok": true }` |

#### Validação de sessão no WebSocket

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.cookies.get("session_token")
    if not auth.is_valid_session(token):
        await websocket.close(code=1008)  # Policy Violation
        return
    await websocket.accept()
    # loop de recebimento de eventos...
```

---

### Módulo 3 — Injeção de Input

**Arquivo:** `app/input_controller.py`  
**Tecnologia:** python-evdev + ydotool

> ⚠️ **Ponto crítico:** No Wayland, ferramentas como `xdotool` e `xte` não funcionam. A solução é escrever eventos diretamente no kernel via `/dev/uinput`, que funciona em X11 e Wayland.

#### Dispositivos virtuais criados

```python
from evdev import UInput, ecodes as e

# Mouse virtual
mouse = UInput({
    e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
}, name='EVE-Mouse')

# Teclado virtual (para teclas especiais como Enter, Backspace etc.)
keyboard = UInput({
    e.EV_KEY: list(range(0, 255)),
}, name='EVE-Mouse-keyboard')
```

#### Funções principais

```python
def move_mouse(dx: float, dy: float):
    mouse.write(e.EV_REL, e.REL_X, int(dx))
    mouse.write(e.EV_REL, e.REL_Y, int(dy))
    mouse.syn()

def click(button: str = 'left'):
    btn = e.BTN_LEFT if button == 'left' else e.BTN_RIGHT
    mouse.write(e.EV_KEY, btn, 1)
    mouse.syn()
    mouse.write(e.EV_KEY, btn, 0)
    mouse.syn()

def scroll(dy: int):
    mouse.write(e.EV_REL, e.REL_WHEEL, dy)
    mouse.syn()

def type_text(text: str):
    # ydotool lida com mapeamento de caracteres UTF-8 automaticamente
    import subprocess
    subprocess.run(['ydotool', 'type', '--', text])
```

> 💡 **Por que `ydotool` para texto?** Mapear manualmente cada caractere Unicode para keycode via evdev é extremamente trabalhoso. O `ydotool type` resolve isso automaticamente.

---

### Módulo 4 — Frontend Mobile

**Arquivo:** `app/static/index.html`  
**Tecnologia:** HTML + CSS + JavaScript vanilla

#### Layout da tela

```
┌─────────────────────────────┐
│  [  Digite aqui...       ]  │  ← toca aqui, abre teclado do celular
├─────────────────────────────┤
│                             │
│                             │
│       ÁREA DE TRACKPAD      │  ← arrastar = mover mouse
│    (toque e arraste)        │
│                             │
│                             │
├──────────────┬──────────────┤
│    [ L ]     │    [ R ]     │  ← clique esquerdo / direito
└──────────────┴──────────────┘
```

#### Lógica JavaScript do trackpad

```javascript
const ws = new WebSocket(`ws://${location.host}/ws`);
const sensitivity = 1.5; // ajustável
let lastTouch = null;

// Movimento do mouse
trackpad.addEventListener('touchmove', (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    if (lastTouch) {
        const dx = (touch.clientX - lastTouch.clientX) * sensitivity;
        const dy = (touch.clientY - lastTouch.clientY) * sensitivity;
        ws.send(JSON.stringify({ type: 'mousemove', dx, dy }));
    }
    lastTouch = touch;
}, { passive: false });

trackpad.addEventListener('touchend', () => { lastTouch = null; });

// Scroll com dois dedos
trackpad.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2) {
        // calcular delta Y entre os dois toques e enviar scroll
    }
});

// Digitação
inputField.addEventListener('input', (e) => {
    if (e.data) {
        ws.send(JSON.stringify({ type: 'keydown', text: e.data }));
    }
    inputField.value = ''; // limpa o campo após enviar
});
```

---

### Módulo 5 — Autenticação

**Arquivo:** `app/auth.py`  
**Tecnologia:** bcrypt + UUID4

#### Fluxo completo

```
1. Usuário acessa http://192.168.x.x:1010
2. Sem cookie válido → redireciona para /login
3. Usuário digita a senha
4. POST /auth/login → valida bcrypt
5. Gera UUID4 como token → armazena em memória com TTL
6. Retorna cookie: session_token=<uuid>; HttpOnly; SameSite=Strict
7. Próximas requisições e o WebSocket verificam o cookie
```

#### Modos de sessão

| Modo | Comportamento |
|---|---|
| **Sessão única** | Token gerado na abertura do app; invalidado ao fechar a janela GTK |
| **Persistente** | Token salvo; ao acessar a URL novamente com o cookie, entra direto |
| **Com expiração** | Token tem TTL em minutos; após expirar, redireciona para login |

---

### Módulo 6 — Configuração

**Arquivo:** `app/config.py`  
**Local do arquivo:** `~/.config/EVE-Mouse/config.json`

```json
{
  "password_hash": "$2b$12$...",
  "port": 1010,
  "session_mode": "persistent",
  "session_timeout_minutes": 0,
  "start_on_boot": false,
  "trackpad_sensitivity": 1.5
}
```

---

## Protocolo WebSocket

Todas as mensagens trocadas entre celular e PC são JSON:

```jsonc
// Mover mouse
{ "type": "mousemove", "dx": 5.2, "dy": -3.1 }

// Clique
{ "type": "click", "button": "left" }   // "left" | "right" | "middle"

// Toque duplo (double click)
{ "type": "dblclick", "button": "left" }

// Scroll
{ "type": "scroll", "dy": -2 }

// Digitar texto
{ "type": "keydown", "text": "Hello World" }

// Teclas especiais
{ "type": "special_key", "key": "enter" }    // "enter" | "backspace" | "tab" | "esc"
```

---

## Instalação e Dependências

### Via DNF (obrigatório para alguns pacotes)

```bash
sudo dnf install python3-gobject gtk4 ydotool python3-pip
sudo systemctl enable --now ydotoold

# Adicionar usuário ao grupo input (requer logout/login depois)
sudo usermod -aG input $USER
```

### Via pip

```bash
pip install fastapi uvicorn[standard] python-evdev bcrypt
```

### `requirements.txt`

```
fastapi
uvicorn[standard]
python-evdev
bcrypt
# PyGObject instalado via DNF, não pip
```

### `EVE-Mouse.desktop` (menu do GNOME)

```ini
[Desktop Entry]
Name=EVE-Mouse
Comment=Controle seu mouse e teclado pelo celular
Exec=/usr/bin/python3 /opt/EVE-Mouse/main.py
Icon=input-mouse
Terminal=false
Type=Application
Categories=Utility;
```

---

## Fluxo de Execução

```
main.py
  │
  ├── Lê config.json
  ├── Inicia FastAPI + Uvicorn em thread separada (daemon=True)
  │     porta 0.0.0.0:1010
  │
  └── Inicia GTK4 na thread principal (obrigatório pelo GTK)
        │
        └── Ao clicar "Iniciar":
              ├── Detecta IP local
              ├── Exibe URL na janela
              └── Servidor já está aceitando conexões
```

```python
# main.py
import threading
import uvicorn
from app.gui import run_gui
from app.server import app as fastapi_app

def start_server():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=1010, log_level="warning")

thread = threading.Thread(target=start_server, daemon=True)
thread.start()

run_gui()  # GTK deve rodar sempre na thread principal
```

---

## Pontos de Atenção

| # | Ponto | Detalhe |
|---|---|---|
| 1 | **Grupo `input`** | O usuário DEVE estar no grupo `input` e fazer logout/login para que o `/dev/uinput` funcione sem `sudo` |
| 2 | **`ydotoold` daemon** | O daemon do ydotool precisa estar ativo para `ydotool type` funcionar. Considere verificar e iniciá-lo programaticamente |
| 3 | **PyGObject via DNF** | Não instalar via `pip` — usar `sudo dnf install python3-gobject` |
| 4 | **GTK na thread principal** | O loop GTK não pode rodar em thread secundária — sempre na `main thread` |
| 5 | **WebSocket e cookie** | Browsers enviam cookies nas conexões WebSocket se estiverem no mesmo domínio/porta — isso funciona nativamente |
| 6 | **Scroll com dois dedos** | Implementar detecção de `e.touches.length === 2` no frontend para mapear scroll |
| 7 | **Segurança** | O app é pensado para rede local. Não expor a porta 1010 para a internet |
| 8 | **Porta fixa 1010** | Manter a porta sempre a mesma para o usuário não precisar reconfigurar o celular |

---

*Documentação gerada para o projeto EVE-Mouse — versão 1.0*
