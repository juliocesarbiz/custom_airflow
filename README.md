# 🚀 Custom Airflow - Orquestrador de DAGs

O **Custom Airflow** é um orquestrador de DAGs (Directed Acyclic Graphs) inspirado no Apache Airflow. Ele permite **criar, gerenciar e executar tarefas programadas**, garantindo dependências entre as execuções e armazenamento de metadados no banco de dados.

---

## 📌 **Recursos**
✅ Cadastro e execução de **DAGs**  
✅ Gerenciamento de **Tarefas** com dependências  
✅ Agendamento via **Crontab** (`croniter`)  
✅ Armazenamento de metadados via **SQLite**  
✅ Suporte a múltiplos estados de execução  
✅ Execução **paralela** de tarefas  
✅ Estruturado para suportar **outros bancos de dados no futuro**  

---


## 🚀 **Como Instalar e Rodar o Projeto**

### **1️⃣ Clonar o repositório**
```bash
git clone https://github.com/seuusuario/custom_airflow.git
cd custom_airflow
```

### **2️⃣ Criar e ativar um ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### **3️⃣ Instalar as dependências**
```bash
pip install -r requirements.txt
```

### **4️⃣ Configurar variáveis de ambiente**
Crie um arquivo **`.env`** na raiz do projeto com o seguinte conteúdo:
```ini
ENV=development
SQLITE_DB=dev.db
PYTHONPATH=D:/Projetos/Python/custom_airflow
```

### **5️⃣ Criar o banco de dados**
Antes de rodar o agendador, certifique-se de que as tabelas do banco foram criadas:
```bash
python -c "from custom_airflow.src.models import Base, get_session; engine = get_session().bind; Base.metadata.create_all(engine)"
```
ou 
```bash
python -m custom_airflow.src.migrate
```

### **6️⃣ Rodar o Agendador**
Para iniciar o **Scheduler**, execute:
```bash
python -m custom_airflow.src.scheduler
```

### **7️⃣ Testar DAGs**
Para testar se uma **DAG está sendo carregada corretamente**, execute:
```bash
python -m custom_airflow.dags.dag_teste
```

---

## 🛠 **Como Criar uma Nova DAG**
Para adicionar uma nova DAG, basta criar um arquivo Python dentro da pasta **`dags/`**, por exemplo:

📌 **`dags/minha_dag.py`**
```python
from custom_airflow.src.dag_parser import DAG, Task
from pathlib import Path

# Define o caminho das tarefas
TASKS_DIR = Path(__file__).resolve().parent.parent / "tasks"

# Criando a DAG
dag = DAG('minha_dag', schedule_interval='*/5 * * * *')  # Executa a cada 5 minutos

# Criando tarefas
task1 = Task(name='task1', script_path=str(TASKS_DIR / 'task1.py'))
task2 = Task(name='task2', script_path=str(TASKS_DIR / 'task2.py'), dependencies=['task1'])

# Adicionando as tarefas à DAG
dag.add_task(task1)
dag.add_task(task2)
```

Agora, basta rodar:

```bash
python -m custom_airflow.dags.minha_dag
```

---

## 📜 **Banco de Dados**
O banco de dados utilizado no modo **desenvolvimento** é o **SQLite (`dev.db`)**, mas o projeto pode ser expandido para suportar **PostgreSQL** ou **MySQL**.

### 📌 **Modelos do Banco**
- `dags`: Armazena as DAGs cadastradas.
- `tasks`: Registra as tarefas dentro das DAGs.
- `executions`: Mantém um histórico de execuções das DAGs.

---

## 🔍 **Validação de Código com `pre-commit`**
Para garantir a qualidade do código, usamos **Pylint** e outros hooks com `pre-commit`.

### **1️⃣ Instalar o `pre-commit`**
```bash
pip install pre-commit
```

### **2️⃣ Instalar os hooks**
```bash
pre-commit install
```

### **3️⃣ Testar os hooks manualmente**
```bash
pre-commit run --all-files
```

Agora, toda vez que você tentar **commitar**, o código será analisado automaticamente.

---

## 🛠 **Possíveis Erros e Soluções**
| Erro | Causa | Solução |
|------|-------|---------|
| `ModuleNotFoundError: No module named 'custom_airflow'` | O Python não está encontrando o pacote. | Rode `python -m custom_airflow.src.scheduler` ao invés de `python custom_airflow/src/scheduler.py`. |
| `sqlite3.OperationalError: no such table: dags` | O banco de dados não foi inicializado. | Rode `python -c "from custom_airflow.src.models import Base, get_session; engine = get_session().bind; Base.metadata.create_all(engine)"`. |
| `pylint import-error` | O `PYTHONPATH` não está definido corretamente. | Adicione `PYTHONPATH=D:/Projetos/Python/custom_airflow` ao `.env` e carregue com `load_dotenv()`. |

---

## 📌 **Futuras Melhorias**
- 🔹 Suporte a **PostgreSQL/MySQL** para produção  
- 🔹 Interface web para visualizar DAGs e execuções  
- 🔹 Notificações via e-mail ou webhook  

---

## 📜 **Licença**
Este projeto é open-source e distribuído sob a licença **MIT**.

---

## 🙌 **Contribuição**
Se quiser contribuir, faça um **fork** do projeto, crie um **pull request** e entre em contato! 😃🚀
