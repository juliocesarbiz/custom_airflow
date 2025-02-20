# test/conftest.py

import sys
import os

# Obter o diretório raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
