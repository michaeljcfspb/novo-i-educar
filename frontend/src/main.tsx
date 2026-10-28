import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "@/App";
import { AuthProvider } from "@/lib/auth";
import "./index.css";

const clienteQuery = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

const raiz = document.getElementById("root");
if (!raiz) throw new Error("Elemento #root não encontrado.");

createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={clienteQuery}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
