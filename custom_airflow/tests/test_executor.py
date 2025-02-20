import pytest
from executor import Executor
from dag_parser import Task

def test_executor_run_success(monkeypatch):
    def mock_run(self):
        pass  # Simula execução bem-sucedida

    monkeypatch.setattr(Executor, 'run', mock_run)
    task = Task(name='task1', script_path='tasks/task1.py')
    executor = Executor(task)
    executor.run()  # Não deve levantar exceção

def test_executor_run_failure(monkeypatch):
    def mock_run(self):
        raise Exception('Erro simulado')

    monkeypatch.setattr(Executor, 'run', mock_run)
    task = Task(name='task1', script_path='tasks/task1.py')
    executor = Executor(task)
    with pytest.raises(Exception):
        executor.run()
