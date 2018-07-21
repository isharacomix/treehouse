from django.urls import path

from . import views

urlpatterns = [
    path(r'', views.Index.as_view(), name='index'),
    path(r'hls/<filename>', views.StreamFragment.as_view(), name='fragment'),
    path(r'login', views.LoginPage.as_view(), name='login'),
    path(r'logout', views.LogoutPage.as_view(), name='logout'),
    path(r'login/<uuid:invitation>', views.InvitationPage.as_view(), name='invitation'),
    path(r'invites', views.InvitationList.as_view(), name='invitation_list'),
    path(r'users', views.UserList.as_view(), name='user_list'),
    path(r'api/status', views.StatusApi.as_view(), name='status'),
    path(r'chat', views.Chatroom.as_view(), name='chatroom'),
    path(r'video', views.Videoroom.as_view(), name='videoroom'),
    path(r'api/chat', views.ChatApi.as_view(), name='chat'),
]
