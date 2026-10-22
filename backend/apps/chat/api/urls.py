from django.urls import path

from apps.chat.api.views import (
    ConversationDetailView,
    ConversationListView,
    FeedbackView,
    SuggestionsView,
)
from apps.chat.views import chat_stream

urlpatterns = [
    path("chat", chat_stream, name="chat"),
    path("conversations", ConversationListView.as_view(), name="conversations"),
    path(
        "conversations/<uuid:conversation_id>",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path("messages/<uuid:message_id>/feedback", FeedbackView.as_view(), name="feedback"),
    path("suggestions", SuggestionsView.as_view(), name="suggestions"),
]
