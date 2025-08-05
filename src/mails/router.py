"""Core of mails with all the endpoints."""

import datetime
from typing import Annotated

import requests
from fastapi import APIRouter, Body, HTTPException, Query
from jinja2 import Environment, PackageLoader
from sqlmodel import select

from src.adapters.vesync.projects.router import read_project
from src.adapters.vesync.projects.models import PMProject
from src.database import SessionDep
from src.mails.models import Mail, MailCreate, MailPublic, MailPublicReadyToBeSent
from src.users.models import User
from src.users.router import refresh_access_token

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


@router.get("/mails/{id}", response_model=MailPublicReadyToBeSent)
async def read_mail(
    id: int,
    session: SessionDep,
):
    """Read a mail."""
    mail: Mail = session.get(Mail, id)

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


@router.post("/mails/{id}/test")
async def test_mail(
    id: int,
    to: Annotated[str, Body(embed=True)],
    session: SessionDep,
):
    """Send mail to somebody for test.

    :param mail_id: The id of the mail to preview.
    :param email: The email to send the preview to.
    :param session: The database session.
    """
    # Get access token of the user from the database.
    user: User = session.exec(select(User).where(User.email == to)).first()

    # If the user is not found, raise an error.
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please login to get a new token.",
        )

    # If the user's token is expired or will expire in less than 5 minutes, refresh it.
    if user.expires_at < datetime.datetime.now().timestamp() + 300:
        user = refresh_access_token(user.id, session)

    # Get email content.
    mail: MailPublicReadyToBeSent = await read_mail(id, session)

    # Send the mail to the email address via microsoft graph API.
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {
        "Authorization": f"Bearer {user.access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "message": {
            "subject": mail.subject,
            "body": {
                "contentType": "HTML",
                "content": mail.body,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to,
                    },
                },
            ],
        },
        "saveToSentItems": True,
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 202:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to send mail, error: {response.text}",
        )
    return {"message": "Mail sent successfully"}
