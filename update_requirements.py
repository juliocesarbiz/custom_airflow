import sys
import subprocess

def update_requirements():
    # Gera o requirements.txt usando o pip do ambiente atual

    with open("requirements.txt", "w", encoding="utf-8") as f:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f, check=True)
    # Adiciona o arquivo gerado ao git
    subprocess.run(["git", "add", "requirements.txt"], check=True)

if __name__ == "__main__":
    update_requirements()
