import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api, ApiError, type Usuario } from "./api";

interface ContextoAuth {
  usuario: Usuario | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
}

const Contexto = createContext<ContextoAuth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let ativo = true;
    api
      .me()
      .then((dados) => {
        if (ativo) setUsuario(dados);
      })
      .catch((erro: unknown) => {
        if (!(erro instanceof ApiError) || ![401, 403].includes(erro.status)) {
          console.error("Falha ao carregar a sessão", erro);
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  const entrar = useCallback(async (email: string, senha: string) => {
    const dados = await api.login(email, senha);
    setUsuario(dados);
  }, []);

  const sair = useCallback(async () => {
    await api.logout();
    setUsuario(null);
  }, []);

  const valor = useMemo(
    () => ({ usuario, carregando, entrar, sair }),
    [usuario, carregando, entrar, sair],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useAuth(): ContextoAuth {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useAuth precisa estar dentro de <AuthProvider>.");
  return contexto;
}
