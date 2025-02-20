from pathlib import Path
from custom_airflow.src.dag_parser import DAG, Task



# Obtém a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent  # Vai para a raiz do projeto

# Diretório das tasks
TASKS_DIR = BASE_DIR / "tasks"

# Criando a DAG
dag = DAG('example_dag', schedule_interval='*/1 * * * *')  # Executa a cada minuto

# Criando as tarefas com caminhos corretos
task1 = Task(
    name='task1',
    script_path=str(TASKS_DIR / 'task1.py'),  # Caminho absoluto
    retries=2,
    timeout=120
)

task2 = Task(
    name='task2',
    script_path=str(TASKS_DIR / 'task2.py'),
    dependencies=['task1'],
    retries=3,
    timeout=90
)

task3 = Task(
    name='task3',
    script_path=str(TASKS_DIR / 'task3.py'),
    dependencies=['task1'],
    retries=1,
    timeout=60
)

# Adicionando as tarefas na DAG
dag.add_task(task1)
dag.add_task(task2)
dag.add_task(task3)
