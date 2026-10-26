"""Pruebas contra PostgreSQL real, en una base separada (<base>_test) del mismo servidor.

La base de prueba se recrea al inicio de la sesión y se migra con Alembic (así también se
prueba la migración). Cada test arranca con las tablas vacías (TRUNCATE ... RESTART IDENTITY).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db import Base, get_db
from app.main import app

URL_PRINCIPAL = make_url(settings.database_url)
URL_PRUEBA = URL_PRINCIPAL.set(database=f"{URL_PRINCIPAL.database}_test")
RAIZ_BACKEND = Path(__file__).resolve().parent.parent


def _recrear_base_de_prueba() -> None:
    admin = create_engine(URL_PRINCIPAL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conexion:
        nombre = URL_PRUEBA.database
        conexion.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
        conexion.execute(text(f'CREATE DATABASE "{nombre}"'))
    admin.dispose()


def _migrar() -> None:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    url = URL_PRUEBA.render_as_string(hide_password=False).replace("%", "%%")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def engine_prueba():
    _recrear_base_de_prueba()
    _migrar()
    engine = create_engine(URL_PRUEBA, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine_prueba):
    return sessionmaker(bind=engine_prueba, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def tablas_vacias(engine_prueba) -> Iterator[None]:
    yield
    tablas = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine_prueba.begin() as conexion:
        conexion.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(session_factory) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def client(session_factory) -> Iterator[TestClient]:
    def get_db_prueba() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = get_db_prueba
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
