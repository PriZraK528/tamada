from django.urls import path

from . import views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("invitations/<str:token>/", views.invitation_accept, name="invitation_accept"),
    path("events/create/", views.event_create, name="event_create"),
    path("profile/", views.profile, name="profile"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
    path("events/<int:pk>/leave/", views.event_leave, name="event_leave"),
]
