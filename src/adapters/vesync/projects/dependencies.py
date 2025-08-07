"""Router dependencies."""

import datetime

from sqlmodel import select

from src.adapters.vesync.projects.exceptions import NoFreshUserError
from src.adapters.vesync.projects.models import PmUser
from src.database import SessionDep


def get_fresh_user(session: SessionDep) -> PmUser:
    """Get the user whose token is not expired and has the latest expires_at."""
    statement = (
        select(PmUser)
        .where(PmUser.expires_at > datetime.datetime.now().timestamp())
        .order_by(PmUser.expires_at.desc())
    )

    user = session.exec(statement).first()

    if not user:
        raise NoFreshUserError()

    return user
