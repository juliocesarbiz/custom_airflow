from .models import Base, get_session

def run_migrations():
    """Cria as tabelas no banco de dados se elas não existirem."""
    engine = get_session().bind
    print(f"Criando tabelas no banco: {engine.url}")
    Base.metadata.create_all(engine)
    print("Migração concluída!")

if __name__ == "__main__":
    run_migrations()
