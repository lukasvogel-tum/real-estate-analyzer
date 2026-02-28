import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQLITE_PATH = os.path.join(BACKEND_DIR, "metadata.db")
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def _is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite")


SQLALCHEMY_DATABASE_URL = _normalize_database_url(DATABASE_URL)
ENGINE_KWARGS = {"future": True}
if _is_sqlite(SQLALCHEMY_DATABASE_URL):
    ENGINE_KWARGS["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **ENGINE_KWARGS)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    project_type: Mapped[str] = mapped_column(String(64), default="potenziell")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["DocumentRecord"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_filename: Mapped[str] = mapped_column(String(512))
    stored_file_path: Mapped[str] = mapped_column(String(2048))
    stored_text_path: Mapped[str] = mapped_column(String(2048))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunks_indexed: Mapped[int] = mapped_column(Integer, default=0)
    extraction_status: Mapped[str] = mapped_column(String(64), default="indexed")
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    project: Mapped[ProjectRecord] = relationship(back_populates="documents")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _as_project_summary(row: Any) -> dict[str, Any]:
    project = getattr(row, "ProjectRecord", None)
    if project is None:
        project = row[0]
    files_count = int(row.files_count or 0)
    chunks_indexed = int(row.chunks_indexed or 0)

    return {
        "project_name": project.project_name,
        "project_type": project.project_type,
        "created_at": _to_iso(project.created_at),
        "updated_at": _to_iso(project.updated_at),
        "files_count": files_count,
        "text_backups_count": files_count,
        "chunks_indexed": chunks_indexed,
    }


def init_metadata_db() -> None:
    os.makedirs(BACKEND_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def _get_or_create_project(
    session: Session, project_name: str, project_type: str | None = None
) -> ProjectRecord:
    cleaned_name = (project_name or "").strip()
    if not cleaned_name:
        raise ValueError("Project name is required.")

    project = session.scalar(
        select(ProjectRecord).where(ProjectRecord.project_name == cleaned_name)
    )
    now = _utc_now()

    if project is None:
        project = ProjectRecord(
            project_name=cleaned_name,
            project_type=(project_type or "potenziell"),
            created_at=now,
            updated_at=now,
        )
        session.add(project)
        session.flush()
        return project

    if project_type:
        project.project_type = project_type
    project.updated_at = now
    session.add(project)
    session.flush()
    return project


def upsert_project_record(project_name: str, project_type: str | None = None) -> dict[str, Any]:
    with SessionLocal() as session:
        project = _get_or_create_project(session, project_name, project_type)
        session.commit()
        return {
            "project_name": project.project_name,
            "project_type": project.project_type,
            "created_at": _to_iso(project.created_at),
            "updated_at": _to_iso(project.updated_at),
        }


def add_document_record(
    project_name: str,
    source_filename: str,
    stored_file_path: str,
    stored_text_path: str,
    file_size_bytes: int | None = None,
    chunks_indexed: int = 0,
    extraction_status: str = "indexed",
    error_message: str | None = None,
    project_type: str | None = None,
) -> None:
    with SessionLocal() as session:
        project = _get_or_create_project(session, project_name, project_type)
        now = _utc_now()
        session.add(
            DocumentRecord(
                project_id=project.id,
                source_filename=source_filename,
                stored_file_path=stored_file_path,
                stored_text_path=stored_text_path,
                file_size_bytes=file_size_bytes,
                chunks_indexed=max(0, int(chunks_indexed or 0)),
                extraction_status=extraction_status,
                error_message=error_message,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def list_project_records() -> list[dict[str, Any]]:
    with SessionLocal() as session:
        statement = (
            select(
                ProjectRecord,
                func.count(DocumentRecord.id).label("files_count"),
                func.coalesce(func.sum(DocumentRecord.chunks_indexed), 0).label("chunks_indexed"),
            )
            .outerjoin(DocumentRecord, ProjectRecord.id == DocumentRecord.project_id)
            .group_by(ProjectRecord.id)
        )
        rows = session.execute(statement).all()
        return [_as_project_summary(row) for row in rows]


def get_project_record(project_name: str) -> dict[str, Any] | None:
    target = (project_name or "").strip()
    if not target:
        return None

    with SessionLocal() as session:
        statement = (
            select(
                ProjectRecord,
                func.count(DocumentRecord.id).label("files_count"),
                func.coalesce(func.sum(DocumentRecord.chunks_indexed), 0).label("chunks_indexed"),
            )
            .outerjoin(DocumentRecord, ProjectRecord.id == DocumentRecord.project_id)
            .where(ProjectRecord.project_name == target)
            .group_by(ProjectRecord.id)
        )
        row = session.execute(statement).one_or_none()
        if row is None:
            return None
        return _as_project_summary(row)
