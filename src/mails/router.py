"""Core of mails with all the endpoints."""

from fastapi import APIRouter

from src.database import SessionDep
from src.mails.models import Mail
from src.mails.schemas import MailIn
from src.projects.router import read_project
from src.projects.schemas import PMProject

router = APIRouter(
    tags=["mails"],
)


@router.post("/mails")
async def create_mail(mail_in: MailIn, session: SessionDep) -> Mail:
    """Create a mail."""
    project: PMProject = await read_project(mail_in.project_id)
    mail_db: Mail = Mail(
        project_name=mail_in.project_name,
        project_managers=",".join(project.project_managers),
        cloud_developers=",".join(project.cloud_developers),
        web_developers=",".join(project.web_developers),
        app_developers=",".join(project.app_developers),
        ui_testers=",".join(project.ui_testers),
    )
    session.add(mail_db)
    session.commit()
    session.refresh(mail_db)
    return mail_db
