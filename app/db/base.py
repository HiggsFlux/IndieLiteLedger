# Import all the models, so that Base has them before being
# imported by Alembic or used by create_all
from app.db.base_class import Base  # noqa
from app.models.client import Client, FollowUp  # noqa
from app.models.order import Order  # noqa
from app.models.payment import PaymentRecord  # noqa
from app.models.cost import Cost  # noqa
from app.models.role import Role  # noqa
from app.models.user import User  # noqa
