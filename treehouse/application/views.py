from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import Http404, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Invite

from datetime import timedelta
from pathlib import Path
from redis import Redis

import json
import time

QUALITY_OPTIONS = {1080: '/hls/1080p/index.m3u8',
                   720: '/hls/720p/index.m3u8',
                   480: '/hls/480p/index.m3u8'}


# Index: if the user is not logged in, make them log in. Otherwise, render
# the stream.
class Index(View):
    def get(self, request):
        if request.user.is_anonymous:
            return redirect('login')

        q = request.GET.get('q', None)
        if q:
            request.session['q'] = q
        else:
            q = request.session.get('q', None)
        stream_src = QUALITY_OPTIONS.get(q, None)
        
        return render(request, 'index.html', {'superuser': request.user.is_superuser, 'stream_src': stream_src})



# Chatroom
class Videoroom(View):
    def get(self, request):
        if request.user.is_anonymous:
            return redirect('login')
        q = request.GET.get('q', None)
        if q:
            request.session['q'] = q
        else:
            q = request.session.get('q', None)
        stream_src = QUALITY_OPTIONS.get(q, None)

        return render(request, 'video.html', {'stream_src': stream_src})

# Chatroom
class Chatroom(View):
    def get(self, request):
        if request.user.is_anonymous:
            return redirect('login')

        return render(request, 'chat.html')


# This fetches stream fragments for logged in users. It's a performance
# bottleneck, but I don't know a better way to authenticate downloading the
# stream bits.
# Make sure all of the directories that need to be readable by this user are,
# in fact, readable!
class StreamFragment(View):
    def get(self, request, filename, directory=None):
        if request.user.is_anonymous:
            return redirect('login')

        r = Redis()
        r.set('treehouse:viewer:%s'%hash(request.user.username), request.user.username, 120)

        if directory:
            directory = directory.replace('.', '')
            filename = directory + '/' + filename

        if filename.endswith('.m3u8'):
            try:
                content = open(settings.STREAMING_ROOT+filename, 'rb').read()
            except:
                raise Http404("")

            response = HttpResponse(content, content_type='application/x-mpegURL')
            return response

        if filename.endswith('.ts'):
            try:
                content = open(settings.STREAMING_ROOT+filename, 'rb').read()
            except:
                raise Http404("")

            response = HttpResponse(content, content_type='video/mp2t')
            return response

        raise Http404("")

# This logs the user out.
class LogoutPage(View):
    def get(self, request):
        logout(request)
        return redirect('login')

    def post(self, request):
        logout(request)
        return redirect('login')

# Log the user in.
class LoginPage(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('index')

        return render(request, 'login.html', {})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('index')

        if 'username' in request.POST and 'password' in request.POST:
            user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
            if user is not None:
                login(request, user)
                return redirect('index')

        return redirect('login')

# This page allows a user to redeem their invitation.
class InvitationPage(View):
    def get(self, request, invitation):
        if request.user.is_authenticated:
            return redirect('index')

        inv = get_object_or_404(Invite, pk=invitation)
        now = timezone.now()

        if now > inv.expires:
            inv.expired = True

        if inv.expired:
            raise Http404("")

        return render(request, 'create.html', {'invitation_id': invitation})

    def post(self, request, invitation):
        if request.user.is_authenticated:
            return redirect('index')

        inv = get_object_or_404(Invite, pk=invitation)
        now = timezone.now()

        if now > inv.expires:
            inv.expired = True

        if inv.expired:
            raise Http404("")

        if 'username' in request.POST and 'password' in request.POST:
            new_user = User.objects.create_user(request.POST['username'], '', request.POST['password'])
            inv.expired = True
            inv.save()
            login(request, new_user)
            return redirect('index')
        else:
            return redirect('login')


# Allow the superuser to list and create new invitations.
class InvitationList(View):
    def get(self, request):
        if request.user.is_anonymous:
            return redirect('login')
        if not request.user.is_superuser:
            return redirect('index')

        invitations = Invite.objects.all()

        return render(request, 'invitations.html', {'invitations': invitations})

    def post(self, request):
        if request.user.is_anonymous:
            return redirect('login')
        if not request.user.is_superuser:
            return redirect('index')

        i = Invite()
        i.expires = timezone.now()+timedelta(days=7)
        i.save()

        return redirect('invitation_list')


# Allow the superuser to list and create new invitations.
class UserList(View):
    def get(self, request):
        if request.user.is_anonymous:
            return redirect('login')
        if not request.user.is_superuser:
            return redirect('index')

        users = User.objects.all()

        return render(request, 'users.html', {'users': users})

    def post(self, request):
        if request.user.is_anonymous:
            return redirect('login')
        if not request.user.is_superuser:
            return redirect('index')

        if 'action' in request.POST:
            if request.POST['action'] == 'delete':
                u = get_object_or_404(User, username=request.POST.get('username', ''))
                if not u.is_superuser:
                    u.delete()

        return redirect('user_list')


# Query the stream status.
@method_decorator(csrf_exempt, name='dispatch')
class StatusApi(View):
    def get(self, request):
        if request.user.is_anonymous:
            return JsonResponse({})

        results = {}
        results['live'] = False
        results['viewers'] = []

        my_file = Path(settings.STREAMING_ROOT+"stream.m3u8")
        if my_file.is_file():
            results['live'] = True

        r = Redis()
        data = r.keys('treehouse:viewer:*')
        for d in data:
            results['viewers'].append((r.get(d) or '').decode('utf-8'))

        return JsonResponse(results)



# Query the chat server.
@method_decorator(csrf_exempt, name='dispatch')
class ChatApi(View):
    def get(self, request):
        if request.user.is_anonymous:
            return JsonResponse({'messages': []})

        age = int(request.GET.get('age', 0))
        r = Redis()
        results = []

        data = r.keys('treehouse:chat:*')
        for d in data:
            t,c,a = d.decode('utf-8').split(':')
            if int(a) > age:
                results.append(json.loads(r.get(d).decode('utf-8')))

        results.sort(key=lambda j: j['age'])
        return JsonResponse({'messages': results})

    def post(self, request):
        if request.user.is_anonymous:
            return JsonResponse({})

        author = request.user.username
        content = request.POST.get('content', '')
        age = int(time.time()*1000)

        if content:
            r = Redis()
            message = {'author': escape(author), 'content': escape(content), 'age': age}
            r.set("treehouse:chat:%d"%age, json.dumps(message), 60*60)

        return JsonResponse({})
