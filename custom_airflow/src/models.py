from enum import Enum as PyEnum
import os
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



load_dotenv()

Base = declarative_base()

class TaskStatus(PyEnum):
    pending = 'pending'
    running = 'running'
    success = 'success'
    failed = 'failed'

class DAGModel(Base):
    __tablename__ = 'dags'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    tasks = relationship('TaskModel', back_populates='dag')
    executions = relationship('ExecutionModel', back_populates='dag')

class TaskModel(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    script_path = Column(String)
    dependencies = Column(String)
    status = Column(Enum(TaskStatus))
    dag_id = Column(Integer, ForeignKey('dags.id'))
    dag = relationship('DAGModel', back_populates='tasks')
    executions = relationship('ExecutionModel', back_populates='task')

class ExecutionModel(Base):
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True)
    dag_id = Column(Integer, ForeignKey('dags.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum(TaskStatus))
    dag = relationship('DAGModel', back_populates='executions')
    task = relationship('TaskModel', back_populates='executions')


def get_session():
    """Retorna a sessão do banco de dados, escolhendo entre SQLite (dev) e
       PostgreSQL (produção)."""
    
    env = os.getenv("ENV", "development")  # Padrão é "development" se a variável não estiver definida
    
    if env == "production":
        # Configuração para PostgreSQL (produção)
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_pass = os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'dag-flow')

        DATABASE_URL = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'

    else:
        # Configuração para SQLite (desenvolvimento)
        db_name = os.getenv('SQLITE_DB', 'dev.db')  # Nome do banco SQLite
        DATABASE_URL = f'sqlite:///{db_name}'  # Caminho local do banco

    # Criar engine e sessão
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    Session = sessionmaker(bind=engine)
    
    return Session()