import pytest
from dag_parser import DAG, Task

def test_add_task():
    dag = DAG('test_dag', schedule_interval='@daily')
    task1 = Task(name='task1', script_path='tasks/task1.py')
    dag.add_task(task1)
    assert 'task1' in dag.tasks

def test_add_task_with_missing_dependency():
    dag = DAG('test_dag', schedule_interval='@daily')
    task1 = Task(name='task1', script_path='tasks/task1.py', dependencies=['task_missing'])
    with pytest.raises(ValueError):
        dag.add_task(task1)
