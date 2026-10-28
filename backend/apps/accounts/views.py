"""Autenticação: sessão (cookie + CSRF) e token DRF."""
from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CsrfObrigatorio
from .serializers import LoginSerializer, TokenSerializer, UsuarioSerializer


class CsrfView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(
        tags=["Autenticação"],
        summary="Obtém o cookie CSRF",
        responses={200: OpenApiResponse(description="Cookie csrftoken definido.")},
    )
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfObrigatorio]

    @extend_schema(
        tags=["Autenticação"],
        summary="Autentica por e-mail e senha (sessão)",
        request=LoginSerializer,
        responses={200: UsuarioSerializer, 400: OpenApiResponse(description="Credenciais inválidas.")},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            username=serializer.validated_data["email"].lower(),
            password=serializer.validated_data["password"],
        )
        if usuario is None or not usuario.is_active:
            return Response(
                {"detail": "E-mail ou senha inválidos."}, status=status.HTTP_400_BAD_REQUEST
            )
        login(request, usuario)
        usuario.registrar_acesso()
        return Response(UsuarioSerializer(usuario).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.Serializer

    @extend_schema(
        tags=["Autenticação"],
        summary="Encerra a sessão",
        responses={204: None},
    )
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Autenticação"], summary="Dados do usuário autenticado", responses=UsuarioSerializer)
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class TokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        tags=["Autenticação"],
        summary="Emite token DRF para integrações",
        request=LoginSerializer,
        responses={200: TokenSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = authenticate(
            request,
            username=serializer.validated_data["email"].lower(),
            password=serializer.validated_data["password"],
        )
        if usuario is None or not usuario.is_active:
            return Response(
                {"detail": "E-mail ou senha inválidos."}, status=status.HTTP_400_BAD_REQUEST
            )
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response({"token": token.key, "perfil": usuario.perfil})
