import os
import sys

# Adiciona o diretório raiz ao sys.path para permitir imports corretamente
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Agora o import deve funcionar corretamente
from src.scheduler import main  # Removendo 'custom_airflow', pois o script está na raiz do projeto

if __name__ == "__main__":
    print("Iniciando o Scheduler...")
    main()  # Chama a função principal do scheduler
