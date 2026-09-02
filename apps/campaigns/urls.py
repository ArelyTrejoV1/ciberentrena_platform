from rest_framework.routers import DefaultRouter

from .views import CampanaViewSet

router = DefaultRouter()
router.register("", CampanaViewSet, basename="campana")

urlpatterns = router.urls
