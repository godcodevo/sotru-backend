from django.urls import path

from backend.ai_service.views import StreamGeneratorView

urlpatterns = [
    path("generate-stream", view=StreamGeneratorView.as_view(), name="streamgeneratorview"),
]