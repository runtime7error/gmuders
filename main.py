"""
Ponto de entrada para o executável GMUD.
Inicia o servidor Uvicorn e abre o navegador automaticamente.
"""

import os
import sys
import webbrowser
import threading
import uvicorn


def open_browser():
    """Abre o navegador após um pequeno delay para o servidor iniciar."""
    import time
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


def main():
    # Garantir que o diretório output exista ao lado do executável
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(os.path.join(exe_dir, "output"), exist_ok=True)

    print("=" * 50)
    print("  GMUD - Gerador de Plano de Implantação")
    print("  Acesse: http://localhost:8000")
    print("=" * 50)
    print()
    print("Pressione Ctrl+C para encerrar.")
    print()

    # Abrir navegador em thread separada
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor
    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
