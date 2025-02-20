import sys
from pathlib import Path
import pytz
import logging


import time
import importlib.util
from dotenv import load_dotenv
import os
from datetime import datetime
from croniter import croniter

from .models import DAGModel, TaskModel, ExecutionModel, get_session, TaskStatus

from .dag_parser import DAG
import schedule



# Configuração do Logging
logging.basicConfig(
    level=logging.INFO,  # Ajuste para DEBUG para mais detalhes
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Obtém o diretório do projeto (raiz do repositório)
BASE_DIR = Path(__file__).resolve().parent



# Carrega as variáveis de ambiente do arquivo .env
dotenv_path = BASE_DIR / '.env'

print ('================================')
print (dotenv_path)
print ('================================')
print ('================================')
print (BASE_DIR)
print ('================================')
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    logger.info(f"Arquivo .env carregado: {dotenv_path}")
else:
    logger.warning(f"Arquivo .env não encontrado: {dotenv_path}")

# Obtém o PYTHONPATH do ambiente
pythonpath = os.getenv('PYTHONPATH')

if pythonpath:
    # Resolve o caminho absoluto baseado no PYTHONPATH definido
    resolved_path = (BASE_DIR / pythonpath).resolve()

    # Evita adicionar duplicatas no sys.path
    if str(resolved_path) not in sys.path:
        sys.path.append(str(resolved_path))

    logger.info(f"PYTHONPATH resolvido: {resolved_path}")

else:
    logger.warning("PYTHONPATH não definido no .env")

# Depuração: Imprimir sys.path
logger.info(f"sys.path: {sys.path}")

# Diretório das DAGs
dags_path = BASE_DIR / 'dags'
logger.info(f"Caminho das DAGs: {dags_path}")

# Mapeamento de DAGs: nome -> {'dag': DAG, 'next_run': datetime}
dag_schedule = {}

def load_dag(dag_file):
    """
    Carrega uma DAG a partir de um arquivo Python.
    
    :param dag_file: Caminho para o arquivo Python da DAG.
    :return: Instância da DAG ou None se não for encontrada.
    """
    logger.info(f"Carregando DAG a partir de: {dag_file.name}")
    spec = importlib.util.spec_from_file_location(dag_file.stem, dag_file)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        if hasattr(module, 'dag'):
            logger.info(f"DAG '{module.dag.name}' carregada com sucesso.")
            return module.dag
        else:
            logger.warning(f"Advertência: {dag_file.name} não define uma variável 'dag'.")
            return None
    except Exception as e:
        logger.error(f"Erro ao carregar {dag_file.name}: {e}")
        return None

def initialize_dags():
    """
    Inicializa todas as DAGs existentes no diretório 'dags'.
    """
    for dag_file in dags_path.glob('*.py'):
        if dag_file.name.startswith('__'):
            continue
        dag = load_dag(dag_file)
        if dag:
            if dag.name not in dag_schedule:
                # Registrar a DAG no banco de dados se ainda não estiver
                session = get_session()
                dag_record = session.query(DAGModel).filter_by(name=dag.name).first()
                if not dag_record:
                    dag_record = DAGModel(name=dag.name)
                    session.add(dag_record)
                    session.commit()
                    logger.info(f"DAG '{dag.name}' registrada no banco de dados.")
                session.close()
                
                # Calcular o próximo horário de execução
                now = datetime.now(pytz.UTC)
                cron = croniter(dag.schedule_interval, now)
                next_run = cron.get_next(datetime)
                
                # Atualizar o mapeamento
                dag_schedule[dag.name] = {
                    'dag': dag,
                    'next_run': next_run,
                    'file_mtime': dag_file.stat().st_mtime
                }
                logger.info(f"DAG '{dag.name}' agendada para próxima execução em {next_run}.")
            else:
                # Verificar se o arquivo da DAG foi modificado
                current_mtime = dag_file.stat().st_mtime
                if current_mtime > dag_schedule[dag.name]['file_mtime']:
                    # Reload a DAG
                    logger.info(f"Detectada modificação na DAG '{dag.name}'. Reloading.")
                    dag_schedule[dag.name]['dag'] = dag
                    dag_schedule[dag.name]['file_mtime'] = current_mtime
                    # Recalcular o próximo run
                    now = datetime.now(pytz.UTC)
                    cron = croniter(dag.schedule_interval, now)
                    next_run = cron.get_next(datetime)
                    dag_schedule[dag.name]['next_run'] = next_run
                    logger.info(f"DAG '{dag.name}' re-scheduled para próxima execução em {next_run}.")

def check_and_run_dags():
    """
    Verifica quais DAGs estão programadas para execução e as executa se necessário.
    """
    now = datetime.now(pytz.UTC)
    for dag_name, info in dag_schedule.items():
        dag = info['dag']
        next_run = info['next_run']
        if now >= next_run:
            logger.info(f"Executando DAG '{dag.name}' agendada para {next_run}.")
            try:
                dag.execute()
                # Recalcular o próximo horário de execução
                cron = croniter(dag.schedule_interval, next_run)
                new_next_run = cron.get_next(datetime)
                dag_schedule[dag.name]['next_run'] = new_next_run
                logger.info(f"DAG '{dag.name}' próxima execução agendada para {new_next_run}.")
            except Exception as e:
                logger.error(f"Erro ao executar DAG '{dag.name}': {e}")
                # Opcional: decidir como lidar com falhas (e.g., retry, alertas)
    
def scan_for_new_dags():
    """
    Scaneia o diretório 'dags' para detectar novos arquivos de DAG ou modificações.
    """
    for dag_file in dags_path.glob('*.py'):
        if dag_file.name.startswith('__'):
            continue
        dag = load_dag(dag_file)
        if dag:
            if dag.name not in dag_schedule:
                # Nova DAG encontrada
                session = get_session()
                dag_record = session.query(DAGModel).filter_by(name=dag.name).first()
                if not dag_record:
                    dag_record = DAGModel(name=dag.name)
                    session.add(dag_record)
                    session.commit()
                    logger.info(f"Nova DAG '{dag.name}' registrada no banco de dados.")
                session.close()
                
                # Calcular o próximo horário de execução
                now = datetime.now(pytz.UTC)
                cron = croniter(dag.schedule_interval, now)
                next_run = cron.get_next(datetime)
                
                # Atualizar o mapeamento
                dag_schedule[dag.name] = {
                    'dag': dag,
                    'next_run': next_run,
                    'file_mtime': dag_file.stat().st_mtime
                }
                logger.info(f"Nova DAG '{dag.name}' agendada para próxima execução em {next_run}.")
            else:
                # Verificar se o arquivo da DAG foi modificado
                current_mtime = dag_file.stat().st_mtime
                if current_mtime > dag_schedule[dag.name]['file_mtime']:
                    # Reload a DAG
                    logger.info(f"Detectada modificação na DAG '{dag.name}'. Reloading.")
                    dag_schedule[dag.name]['dag'] = dag
                    dag_schedule[dag.name]['file_mtime'] = current_mtime
                    # Recalcular o próximo run
                    now = datetime.now(pytz.UTC)
                    cron = croniter(dag.schedule_interval, now)
                    next_run = cron.get_next(datetime)
                    dag_schedule[dag.name]['next_run'] = next_run
                    logger.info(f"DAG '{dag.name}' re-scheduled para próxima execução em {next_run}.")

def main():
    # Inicializa as DAGs existentes
    initialize_dags()
    
    logger.info("Scheduler iniciado. Aguardando tarefas...")
    
    while True:
        # Escanear e carregar novas DAGs ou atualizações
        scan_for_new_dags()
        
        # Verificar e executar DAGs que estão programadas para rodar
        check_and_run_dags()
        
        # Aguardar 15 segundos antes de próxima verificação
        time.sleep(15)

if __name__ == '__main__':
    main()
