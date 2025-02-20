from src.dag_parser import DAG, Task

# Defina a expressão cron ou intervalos específicos
# Exemplos:
# - '@hourly' para executar a cada hora
# - '*/5 * * * *' para executar a cada 5 minutos
# - '0 0 * * *' para executar diariamente à meia-noite

dag = DAG('example_dag', schedule_interval='*/1 * * * *')  # Executa a cada minuto

task1 = Task(
    name='task1',
    script_path='tasks/task1.py',
    retries=2,
    timeout=120
)

task2 = Task(
    name='task2',
    script_path='tasks/task2.py',
    dependencies=['task1'],
    retries=3,
    timeout=90
)

task3 = Task(
    name='task3',
    script_path='tasks/task3.py',
    dependencies=['task1'],
    retries=1,
    timeout=60
)

dag.add_task(task1)
dag.add_task(task2)
dag.add_task(task3)
