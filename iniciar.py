"""
Abre a interface do projeto com um único comando:

    python iniciar.py

Sobe o backend (Flask, porta 5000) e o frontend (Vite, porta 5173),
espera os dois ficarem prontos e abre o site no navegador.
Para encerrar tudo, aperte Ctrl+C nesta janela.
"""

import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
FRONTEND = RAIZ / "frontend"
PORTA_BACKEND = 5000
PORTA_FRONTEND = 5173
URL = f"http://localhost:{PORTA_FRONTEND}"


def porta_aberta(porta):
    """True se já existe algum servidor escutando nessa porta."""
    try:
        with socket.create_connection(("localhost", porta), timeout=0.5):
            return True
    except OSError:
        return False


def iniciar(comando, pasta):
    """Inicia um processo em segundo plano, num grupo próprio (para poder encerrá-lo depois)."""
    if os.name == "nt":
        return subprocess.Popen(comando, cwd=pasta, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    return subprocess.Popen(comando, cwd=pasta, start_new_session=True)


def encerrar(processo):
    """Encerra o processo e os filhos dele (o Flask em modo debug cria um processo filho)."""
    if processo.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(processo.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.killpg(processo.pid, signal.SIGTERM)


def esperar_porta(porta, processo, nome, limite=60):
    """Espera o servidor responder na porta. Falha se o processo morrer ou demorar demais."""
    inicio = time.time()
    while time.time() - inicio < limite:
        if porta_aberta(porta):
            return
        if processo is not None and processo.poll() is not None:
            raise RuntimeError(f"O {nome} fechou com erro (veja as mensagens acima).")
        time.sleep(0.5)
    raise RuntimeError(f"O {nome} não respondeu na porta {porta} em {limite} s.")


def main():
    npm = shutil.which("npm")
    if npm is None:
        sys.exit("Node.js/npm não encontrado. Instale em https://nodejs.org e tente de novo.")

    # Na primeira vez, instala as dependências do frontend
    if not (FRONTEND / "node_modules").is_dir():
        print("Instalando dependências do frontend (só na primeira vez)...")
        subprocess.run([npm, "install"], cwd=FRONTEND, check=True)

    processos = []
    try:
        # Backend
        backend = None
        if porta_aberta(PORTA_BACKEND):
            print(f"Backend já está rodando na porta {PORTA_BACKEND}.")
        else:
            print("Iniciando o backend (Flask)...")
            backend = iniciar([sys.executable, str(RAIZ / "backend" / "app.py")], RAIZ)
            processos.append(backend)

        # Frontend
        frontend = None
        if porta_aberta(PORTA_FRONTEND):
            print(f"Frontend já está rodando na porta {PORTA_FRONTEND}.")
        else:
            print("Iniciando o frontend (Vite)...")
            frontend = iniciar([npm, "run", "dev", "--", "--port", str(PORTA_FRONTEND), "--strictPort"], FRONTEND)
            processos.append(frontend)

        esperar_porta(PORTA_BACKEND, backend, "backend")
        esperar_porta(PORTA_FRONTEND, frontend, "frontend")

        print(f"\nInterface pronta: {URL}")
        webbrowser.open(URL)

        if not processos:
            return  # Os dois já estavam rodando: só abre o navegador

        print("Aperte Ctrl+C para encerrar.\n")
        while all(p.poll() is None for p in processos):
            time.sleep(1)
        print("Um dos servidores parou. Encerrando...")

    except KeyboardInterrupt:
        print("\nEncerrando...")
    except RuntimeError as erro:
        print(f"\nErro: {erro}")
    finally:
        for processo in processos:
            encerrar(processo)


if __name__ == "__main__":
    main()
