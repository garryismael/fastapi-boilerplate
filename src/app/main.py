from app import router
from app.configuration import settings
from app.setup import create_application

app = create_application(router=router, settings=settings)
