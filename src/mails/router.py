"""Core of mails with all the endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from jinja2 import Environment, PackageLoader
from sqlmodel import select

from src.database import SessionDep
from src.mails.models import Mail, MailCreate, MailPublic, MailPublicReadyToBeSent
from src.projects.router import read_project
from src.projects.schemas import PMProject

router = APIRouter(
    tags=["mails"],
)


@router.post("/mails", response_model=MailPublic)
async def create_mail(mail_create: MailCreate, session: SessionDep):
    """Create a mail."""
    project: PMProject = await read_project(mail_create.project_id)
    mail_db: Mail = Mail(
        project_name=mail_create.project_name,
        conclusion=mail_create.conclusion,
        risk=mail_create.risk,
        suggestion=mail_create.suggestion,
        project_managers=",".join(project.project_managers),
        api_testers=",".join(project.api_testers),
        cloud_developers=",".join(project.cloud_developers),
        web_developers=",".join(project.web_developers),
        app_developers=",".join(project.app_developers),
        ui_testers=",".join(project.ui_testers),
    )
    session.add(mail_db)
    session.commit()
    session.refresh(mail_db)
    return mail_db


@router.get("/mails", response_model=list[MailPublic])
async def read_mails(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    """Read mails."""
    mails = session.exec(select(Mail).offset(offset).limit(limit)).all()
    return mails


@router.get("/mails/{mail_id}", response_model=MailPublicReadyToBeSent)
async def read_mail(
    mail_id: int,
    session: SessionDep,
):
    """Read a mail."""
    mail: Mail = session.get(Mail, mail_id)

    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    # Set 'to' to the project managers and cloud developers if they exist.
    to = []
    if mail.project_managers:
        to.extend(mail.project_managers.split(","))
    if mail.cloud_developers:
        to.extend(mail.cloud_developers.split(","))

    # Set 'cc' to the web developers, app developers, and ui testers if they exist.
    cc = []
    if mail.web_developers:
        cc.extend(mail.web_developers.split(","))
    if mail.app_developers:
        cc.extend(mail.app_developers.split(","))
    if mail.ui_testers:
        cc.extend(mail.ui_testers.split(","))

    # Set 'subject' to the project name.
    subject = mail.project_name

    # Render the body of the mail.
    env = Environment(
        loader=PackageLoader("src.mails"),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("report.jinja")

    body = template.render(
        {
            "conclusion": mail.conclusion,
            "project_name": mail.project_name,
            "api_testers": mail.api_testers,
            "cloud_developers": mail.cloud_developers,
        }
    )

    return MailPublicReadyToBeSent(
        to=to,
        cc=cc,
        subject=subject,
        body=body,
    )
