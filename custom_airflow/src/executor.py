import os
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Executor:
    def __init__(self, task, retries=3, timeout=60):
        self.task = task
        self.venv_dir = Path('venvs') / self.task.name
        self.retries = retries
        self.timeout = timeout  # Tempo máximo em segundos

    def setup_venv(self):
        if not self.venv_dir.exists():
            logger.info(f"Configurando ambiente virtual para a tarefa '{self.task.name}'.")
            subprocess.check_call([sys.executable, '-m', 'venv', str(self.venv_dir)])
            # Instale dependências específicas se necessário
            # subprocess.check_call([str(self.venv_dir / 'Scripts' / 'pip'), 'install', '-r', 'requirements.txt'])
            logger.info(f"Ambiente virtual configurado para a tarefa '{self.task.name}'.")

    def run(self):
        try:
            logger.info(f"Iniciando execução da tarefa '{self.task.name}'.")
            self.task.status = 'running'
            self.setup_venv()
            # Executa o script no venv
            if os.name == 'nt':
                python_executable = self.venv_dir / 'Scripts' / 'python.exe'
            else:
                python_executable = self.venv_dir / 'bin' / 'python'

            # Iniciar a tarefa com timeout
            result = subprocess.run(
                [str(python_executable), self.task.script_path],
                check=True,
                timeout=self.timeout
            )
            self.task.status = 'success'
            logger.info(f"Tarefa '{self.task.name}' concluída com sucesso.")
        except subprocess.TimeoutExpired:
            self.task.status = 'failed'
            logger.error(f"Erro: A tarefa '{self.task.name}' excedeu o tempo máximo de execução ({self.timeout} segundos).")
            raise
        except subprocess.CalledProcessError as e:
            self.task.status = 'failed'
            logger.error(f"Erro ao executar a tarefa '{self.task.name}': {e}")
            raise
