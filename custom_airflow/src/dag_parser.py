import logging
from collections import defaultdict
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pytz

from .executor import Executor
from .models import DAGModel, TaskModel, ExecutionModel, get_session, TaskStatus


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

class Task:
    def __init__(self, name: str, script_path: str, dependencies: List[str] = [], retries: int = 3, timeout: int = 60):
        self.name = name
        self.script_path = script_path
        self.dependencies = dependencies
        self.status = 'pending'  # Pode ser 'pending', 'running', 'success', 'failed'
        self.retries = retries
        self.timeout = timeout

class DAG:
    def __init__(self, name: str, schedule_interval: str):
        self.name = name
        self.schedule_interval = schedule_interval  # Expressão cron
        self.tasks: Dict[str, Task] = {}
        self.timezone = pytz.UTC  # Defina o fuso horário conforme necessário

    def add_task(self, task: Task):
        # Validar se as dependências referenciadas existem
        for dep in task.dependencies:
            if dep not in self.tasks:
                logger.error(f"A tarefa '{dep}' referenciada como dependência na tarefa '{task.name}' não existe.")
                raise ValueError(f"A tarefa '{dep}' referenciada como dependência na tarefa '{task.name}' não existe.")
        self.tasks[task.name] = task
        logger.info(f"Tarefa '{task.name}' adicionada à DAG '{self.name}' com dependências: {task.dependencies}")

    def execute_task(self, task: Task, dag_record):
        session = get_session()
        executor = Executor(task, retries=task.retries, timeout=task.timeout)
        
        # Verificar se a tarefa já está registrada no banco de dados
        task_record = session.query(TaskModel).filter_by(name=task.name, dag_id=dag_record.id).first()
        if not task_record:
            # Registrar a tarefa na tabela 'tasks'
            task_record = TaskModel(
                name=task.name,
                script_path=task.script_path,
                dependencies=','.join(task.dependencies) if task.dependencies else '',
                status=TaskStatus.pending,
                dag_id=dag_record.id
            )
            session.add(task_record)
            session.commit()
            logger.info(f"Tarefa '{task.name}' registrada no banco de dados com ID {task_record.id}.")
        
        # Registrar a execução
        execution_record = ExecutionModel(
            dag_id=dag_record.id,
            task_id=task_record.id,  # Associa a execução à tarefa
            start_time=datetime.utcnow(),
            status=TaskStatus.running
        )
        session.add(execution_record)
        session.commit()
        logger.info(f"Execução iniciada para tarefa '{task.name}' da DAG '{self.name}' (Exec ID: {execution_record.id}).")

        attempt = 0
        while attempt < task.retries:
            try:
                executor.run()
                # Atualizar execução
                execution_record.end_time = datetime.utcnow()
                execution_record.status = TaskStatus.success
                session.commit()
                logger.info(f"Tarefa '{task.name}' concluída com sucesso.")
                break  # Saia do loop se a tarefa for bem-sucedida
            except Exception as e:
                attempt += 1
                logger.warning(f"Tentativa {attempt} para tarefa '{task.name}' falhou com erro: {e}")
                if attempt >= task.retries:
                    # Atualizar execução com falha
                    execution_record.end_time = datetime.utcnow()
                    execution_record.status = TaskStatus.failed
                    session.commit()
                    logger.error(f"Tarefa '{task.name}' falhou após {task.retries} tentativas.")
        session.close()

    def execute(self):
        try:
            # Construir o gráfico de dependências e contagem de graus de entrada
            in_degree = defaultdict(int)
            graph = defaultdict(list)

            for task in self.tasks.values():
                for dep in task.dependencies:
                    graph[dep].append(task.name)
                    in_degree[task.name] += 1

            # Inicializar tarefas com grau de entrada zero (sem dependências)
            ready_tasks = [task_name for task_name in self.tasks if in_degree[task_name] == 0]

            session = get_session()
            dag_record = session.query(DAGModel).filter_by(name=self.name).first()

            if not dag_record:
                dag_record = DAGModel(name=self.name)
                session.add(dag_record)
                session.commit()
                logger.info(f"DAG '{self.name}' registrada no banco de dados.")

            with ThreadPoolExecutor(max_workers=5) as executor_pool:
                futures = {}
                # Submeter tarefas prontas para execução
                for task_name in ready_tasks:
                    task = self.tasks[task_name]
                    future = executor_pool.submit(self.execute_task, task, dag_record)
                    futures[future] = task_name
                    logger.info(f"Tarefa '{task_name}' submetida para execução.")

                while futures:
                    # Aguarda a conclusão de qualquer tarefa
                    for future in as_completed(futures):
                        task_name = futures.pop(future)
                        try:
                            future.result()
                            logger.info(f"Tarefa '{task_name}' concluída.")
                            # Atualizar o grau de entrada das tarefas dependentes
                            for dependent_task_name in graph.get(task_name, []):
                                in_degree[dependent_task_name] -= 1
                                if in_degree[dependent_task_name] == 0:
                                    # Submeter a tarefa dependente para execução
                                    dependent_task = self.tasks[dependent_task_name]
                                    future_dep = executor_pool.submit(self.execute_task, dependent_task, dag_record)
                                    futures[future_dep] = dependent_task_name
                                    logger.info(f"Tarefa '{dependent_task_name}' submetida para execução.")
                        except Exception as e:
                            logger.error(f"Tarefa '{task_name}' falhou com erro: {e}")
                        break  # Sair do loop para verificar os próximos futures

            logger.info(f"Execução da DAG '{self.name}' concluída.")

        except Exception as e:
            logger.critical(f"Erro ao executar a DAG '{self.name}': {e}")
        finally:
            session.close()
