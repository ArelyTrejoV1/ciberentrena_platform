from rest_framework.routers import DefaultRouter

from .views import ScoreRiesgoViewSet

router = DefaultRouter()
router.register("", ScoreRiesgoViewSet, basename="score-riesgo")

urlpatterns = router.urls
