# ✨ OmniDoc AI

> Assistente corporativo inteligente com RAG multi-escopo, autenticação JWT, controle de acesso por roles e armazenamento em nuvem (AWS S3).

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura)
- [Funcionalidades](#-funcionalidades)
- [Stack Tecnológico](#-stack-tecnológico)
- [Aprendizados e Desafios](#-aprendizados-e-desafios)
- [Objetivos Alcançados](#-objetivos-alcançados)
- [Como Rodar o Projeto](#-como-rodar-o-projeto)

---

## 💡 Sobre o Projeto

O **OmniDoc AI** é um projeto de estudo desenvolvido para explorar na prática conceitos modernos de Inteligência Artificial aplicada, como RAG (_Retrieval-Augmented Generation_), embeddings vetoriais e integração com LLMs.

A proposta foi construir, do zero, um assistente de IA capaz de:

1. **Entender documentos carregados** — um admin faz o upload de PDFs e todos os colaboradores passam a ter acesso ao conhecimento contido neles.
2. **Isolar documentos pessoais** — cada usuário pode enviar seus próprios PDFs, visíveis apenas para si, para complementar as consultas com contexto privado.
3. **Responder de forma inteligente** — o RAG busca automaticamente nos documentos mais relevantes antes de responder, sem que o usuário precise selecionar nada manualmente.
4. **Manter memória da conversa** — o histórico de cada usuário é persistido no banco de dados, garantindo contexto entre sessões diferentes.

---

## 🏗 Arquitetura

```
┌─────────────────────┐         ┌──────────────────────────────────────┐
│   Frontend          │  HTTP   │   Backend (FastAPI)                   │
│   Streamlit         │◄───────►│                                       │
│                     │         │  /auth    → login, register, me       │
│  - Login/Register   │         │  /documents → upload, list, delete    │
│  - Chat com memória │         │  /chat    → RAG + histórico           │
│  - Upload de PDF    │         │  /users   → gerenciamento             │
│  - Painel Admin     │         └──────┬───────────────┬────────────────┘
└─────────────────────┘                │               │
                                       │               │
                              ┌────────▼───────┐  ┌───▼──────────┐
                              │  PostgreSQL     │  │  ChromaDB    │
                              │                │  │              │
                              │  - users       │  │  Embeddings  │
                              │  - documents   │  │  vetoriais   │
                              │  - chat_history│  │  por escopo  │
                              └────────────────┘  └──────────────┘
                                                          ▲
                                                          │ embed + query
                                                   ┌──────┴───────┐
                                                   │  Google      │
                                                   │  Gemini API  │
                                                   │              │
                                                   │  - Embedding │
                                                   │  - LLM Chat  │
                                                   └──────────────┘
                                       │
                              ┌────────▼───────┐
                              │   AWS S3       │
                              │                │
                              │  company/      │
                              │  personal/     │
                              │    user_{id}/  │
                              └────────────────┘
```

### Fluxo de uma Consulta (RAG)

```
Usuário digita pergunta
        │
        ▼
Backend carrega últimos 10 turnos do histórico (PostgreSQL)
        │
        ▼
Pergunta é convertida em vetor (Gemini Embedding)
        │
        ├──► Busca documentos da empresa (ChromaDB, scope=company, top 4)
        │
        └──► Busca documentos pessoais do usuário (ChromaDB, scope=personal, top 3)
                        │
                        ▼
          Chunks relevantes + histórico → prompt estruturado → Gemini LLM
                        │
                        ▼
                   Resposta ao usuário
                        │
                        ▼
              Salva turno no PostgreSQL (memória persistente)
```

---

## ✅ Funcionalidades

### Autenticação e Segurança

- [x] Registro e login com email/senha (hash bcrypt)
- [x] Autenticação via JWT (Bearer token, 8h de expiração)
- [x] Sessão persistida em cookie no navegador
- [x] Primeiro usuário cadastrado vira admin automaticamente

### Controle de Acesso (RBAC)

- [x] Role **Admin**: faz upload de documentos para a base da empresa, visíveis a todos
- [x] Role **User**: envia documentos pessoais, visíveis apenas para si
- [x] Endpoints protegidos por dependências FastAPI (`get_current_user`, `get_admin_user`)

### Gestão de Documentos

- [x] Upload de PDF com armazenamento no **AWS S3**
- [x] Processamento assíncrono: extração de texto → chunking → embedding → ChromaDB
- [x] Metadados de escopo (`company` / `personal`) gravados em cada chunk vetorial
- [x] Deleção remove o arquivo do S3 e os chunks do ChromaDB simultaneamente
- [x] Batching de embeddings (20 chunks/lote) com retry exponencial para respeitar rate limit da API

### Chat com Memória

- [x] RAG multi-escopo automático: busca em documentos da empresa + documentos pessoais do usuário sem seleção manual
- [x] Histórico de conversa por usuário salvo no PostgreSQL
- [x] Os últimos 10 turnos são injetados no prompt para dar memória contextual à IA
- [x] Restauração do histórico ao reabrir a aplicação
- [x] Prompt inteligente com 4 regras: prioriza documentos, complementa com conhecimento geral quando necessário, nunca inventa dados corporativos

### Interface

- [x] Tela de login/registro com abas
- [x] Sidebar com painel administrativo (admin) e documentos pessoais (todos os usuários)
- [x] Badge visual de role (ADMIN / USER)
- [x] Upload de PDF integrado na área de chat (pill compacto "📎 Anexar PDF")
- [x] Chip de confirmação do arquivo selecionado antes do envio
- [x] Botão de limpar arquivo com reset dinâmico do widget

---

## 🛠 Stack Tecnológico

| Camada              | Tecnologia                   | Finalidade                                                   |
| ------------------- | ---------------------------- | ------------------------------------------------------------ |
| **Backend**         | FastAPI                      | API REST assíncrona                                          |
| **ORM**             | SQLAlchemy                   | Mapeamento objeto-relacional                                 |
| **Banco de Dados**  | PostgreSQL                   | Usuários, documentos e histórico de chat                     |
| **Vector Store**    | ChromaDB                     | Armazenamento e busca de embeddings                          |
| **LLM + Embedding** | Google Gemini API            | `gemini-2.5-flash` (chat) + `gemini-embedding-001` (vetores) |
| **RAG Framework**   | LangChain                    | Carregamento de PDF, chunking, integração com Gemini         |
| **Armazenamento**   | AWS S3 + boto3               | Persistência dos arquivos PDF em nuvem                       |
| **Autenticação**    | python-jose + bcrypt         | JWT e hash de senhas                                         |
| **Frontend**        | Streamlit                    | Interface conversacional                                     |
| **Sessão**          | streamlit-cookies-controller | Persistência de login via cookie                             |

---

## 📚 Aprendizados e Desafios

### RAG na prática

Implementar RAG do zero foi o principal aprendizado do projeto. Entender que a qualidade da resposta depende diretamente de três fatores — qualidade do chunking, relevância dos embeddings e clareza do prompt — foi fundamental para evoluir de respostas genéricas para respostas realmente úteis.

### Multi-escopo com isolamento por usuário

O desafio de separar documentos corporativos (acessíveis a todos) de documentos pessoais (isolados por `user_id`) foi resolvido através de metadados no ChromaDB com filtros compostos `$and` nas queries vetoriais.

### Memória conversacional persistente

A IA por padrão é stateless. Para dar memória real ao assistente, foi necessário persistir cada turno no PostgreSQL e recuperar os últimos N turnos a cada nova mensagem, injetando o histórico no prompt de forma estruturada.

### Rate limiting com retry inteligente

A API gratuita do Gemini tem limite de 100 requisições/minuto. Documentos grandes geravam centenas de chunks, causando erros `429 RESOURCE_EXHAUSTED`. A solução foi implementar processamento em lotes (20 chunks) com backoff exponencial e leitura do `retryDelay` sugerido pela própria API.

### Autenticação sem frameworks prontos

Em vez de usar bibliotecas de autenticação de alto nível, foi implementado o fluxo completo manualmente: hash bcrypt, geração de JWT, middleware de validação no FastAPI via `Depends()` e leitura do token via `Authorization: Bearer` header. Isso trouxe entendimento profundo do protocolo.

### Incompatibilidade passlib + bcrypt 5.x

A biblioteca `passlib` (padrão de mercado para hash de senhas em Python) é incompatível com versões modernas do `bcrypt`. A solução foi usar o `bcrypt` diretamente, sem camadas de abstração, o que reforçou o aprendizado sobre como o hash de senhas realmente funciona.

### Sessão no Streamlit

O Streamlit re-executa o script inteiro a cada interação do usuário, o que destrói o estado. Persistir a sessão via cookie exigiu entender o ciclo de vida do framework: o cookie precisa ser definido **antes** de qualquer `st.rerun()`, pois o rerun interrompe a execução do JavaScript subjacente antes que o cookie seja gravado.

### Armazenamento em nuvem com S3

Integrar o AWS S3 substituiu completamente o armazenamento local. O fluxo ficou: frontend envia arquivo → FastAPI lê bytes em memória → S3 armazena → ChromaDB recebe o arquivo via download temporário para processamento. Isso tornou a aplicação stateless no servidor, pronta para deploy em ambientes sem disco persistente.

---

## 🎯 Objetivos Alcançados

- **Arquitetura desacoplada**: frontend e backend se comunicam exclusivamente via API REST, permitindo substituir qualquer camada independentemente
- **Segurança por camadas**: senhas nunca armazenadas em texto plano, tokens JWT com expiração, endpoints protegidos por role
- **Escalabilidade de dados**: armazenamento de arquivos em S3 (sem limite de disco local), embeddings em ChromaDB (otimizado para busca semântica), dados relacionais em PostgreSQL
- **Experiência de usuário fluida**: RAG automático sem configuração manual, memória conversacional, interface limpa e responsiva
- **Resiliência**: retry com backoff em chamadas de API externas, limpeza de chunks órfãos no ChromaDB, tratamento de erros em cascata (S3 → ChromaDB → PostgreSQL)

---

## 🚀 Como Rodar o Projeto

### Pré-requisitos

- Python 3.10+
- PostgreSQL instalado e rodando
- Conta Google Cloud com Gemini API habilitada
- Conta AWS com bucket S3 criado e usuário IAM com permissão `AmazonS3FullAccess`

### 1. Clonar e criar o ambiente virtual

```bash
git clone https://github.com/seu-usuario/omnidoc-ai.git
cd omnidoc-ai

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/omnidoc-ai

# Google Gemini
GOOGLE_API_KEY=sua-chave-aqui

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=nome-do-seu-bucket
```

> **Como obter as chaves:**
>
> - **Google API Key**: [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials → Create API Key → habilite a "Generative Language API"
> - **AWS Keys**: Console AWS → IAM → Users → Security credentials → Create access key

### 4. Criar o banco de dados PostgreSQL

```sql
CREATE DATABASE "omnidoc-ai";
```

As tabelas são criadas automaticamente pelo SQLAlchemy na primeira inicialização do backend.

> Se você já tem um banco com dados antigos (sem as colunas `hashed_password`, `role`, `scope`), execute o script de migração:
>
> ```bash
> python migrate.py
> ```

### 5. Iniciar o Backend

```bash
uvicorn backend.main:app --reload
```

O backend estará disponível em: `http://127.0.0.1:8000`  
Documentação interativa (Swagger): `http://127.0.0.1:8000/docs`

### 6. Iniciar o Frontend

Em outro terminal (com o venv ativado):

```bash
streamlit run frontend/app.py
```

O frontend estará disponível em: `http://localhost:8501`

### 7. Primeiro acesso

1. Acesse `http://localhost:8501`
2. Clique em **Registrar** e crie sua conta — o **primeiro usuário cadastrado vira admin automaticamente**
3. Faça login e comece a usar

---

## 📁 Estrutura do Projeto

```
omnidoc-ai/
├── backend/
│   ├── api/
│   │   ├── auth.py          # Registro, login, /me
│   │   ├── chat.py          # Endpoint de chat + histórico
│   │   ├── documents.py     # Upload, listagem e deleção de documentos
│   │   └── user.py          # Gerenciamento de usuários
│   ├── core/
│   │   ├── config.py        # Variáveis de ambiente
│   │   ├── deps.py          # Dependências FastAPI (auth guards)
│   │   └── security.py      # JWT e bcrypt
│   ├── db/
│   │   └── database.py      # Conexão SQLAlchemy
│   ├── models/
│   │   └── models.py        # ORM: User, Document, ChatHistory
│   ├── services/
│   │   ├── chat_service.py       # Lógica RAG + prompt
│   │   ├── document_processor.py # Pipeline PDF → chunks → embeddings → ChromaDB
│   │   └── s3_service.py         # Upload, download e delete no AWS S3
│   ├── vector_store/
│   │   └── chroma_client.py # Cliente ChromaDB singleton
│   └── main.py              # Entry point FastAPI
├── frontend/
│   └── app.py               # Interface Streamlit completa
├── migrate.py               # Script de migração de banco
├── cleanup_chroma.py        # Remove chunks órfãos do ChromaDB
├── requirements.txt
└── .env                     # Variáveis de ambiente (não versionar!)
```

---

## ⚠️ Observações

- O arquivo `.env` **nunca deve ser commitado** no repositório. Adicione-o ao `.gitignore`.
- O diretório `chroma_db/` contém o banco vetorial local. Pode ser ignorado no git se preferir recriar os embeddings a cada clone.
- A API gratuita do Gemini tem limite de 100 requisições/minuto. PDFs grandes podem levar alguns minutos para ser indexados devido ao rate limiting com backoff automático.

---

_Desenvolvido com FastAPI, Streamlit, LangChain, Google Gemini, ChromaDB, PostgreSQL e AWS S3._
