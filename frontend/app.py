import streamlit as st
import requests
from streamlit_cookies_controller import CookieController

# ─────────────────────────────────────────────
# Configuração Global
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OmniDoc AI",
    page_icon="✨",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# Cookie manager
cookie_manager = CookieController()
# Lê o cookie UMA vez no topo — na 1ª execução pode ser None (JS ainda carregando),
# na 2ª execução (rerun automático do componente) já retorna o valor real.
_saved_token = cookie_manager.get("omnidoc_token")

# ─────────────────────────────────────────────
# CSS Customizado
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Esconde só o que não queremos — sem tocar no container do botão da sidebar */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stDeployButton"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Badge de role */
    .role-badge-admin {
        background-color: #7c3aed;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .role-badge-user {
        background-color: #0ea5e9;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }

    /* ─── Uploader como botão de clipe compacto ─── */

    /* Remove espaçamento externo do bloco do uploader */
    [data-testid="stFileUploader"] {
        margin-bottom: -8px !important;
    }

    /* Sem visual de drop zone */
    [data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        min-height: unset !important;
    }

    /* Dropzone → pill minimalista "📎 Anexar PDF" */
    [data-testid="stFileUploaderDropzone"] {
        min-height: 36px !important;
        height: 36px !important;
        width: auto !important;
        max-width: 160px !important;
        border-radius: 18px !important;
        border: 1px dashed rgba(255,255,255,0.22) !important;
        background: rgba(255,255,255,0.04) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        padding: 0 14px !important;
        transition: background 0.2s, border-color 0.2s !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        background: rgba(255,255,255,0.09) !important;
        border-color: rgba(255,255,255,0.45) !important;
    }

    /* Esconde texto de instruções e botão "Browse files" */
    [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
    [data-testid="stFileUploaderDropzone"] button         { display: none !important; }

    /* Rótulo visual via pseudo-element */
    [data-testid="stFileUploaderDropzone"]::after {
        content: "📎  Anexar PDF";
        font-size: 12px;
        color: rgba(255,255,255,0.45);
        white-space: nowrap;
        pointer-events: none;
    }

    /* Preview nativo quando arquivo está selecionado: escondemos — usamos o chip abaixo */
    [data-testid="stFileUploaderDeleteBtn"] { display: none !important; }
    [data-testid="stFileUploader"] [class*="uploadedFile"] {
        display: none !important;
    }

    /* Chip do arquivo selecionado */
    .file-chip-bar {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(14, 165, 233, 0.13);
        border: 1px solid rgba(14, 165, 233, 0.32);
        border-radius: 18px;
        padding: 4px 12px;
        font-size: 12px;
        color: #7dd3fc;
        max-width: 80%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State + Restauração de Sessão via Cookie
# ─────────────────────────────────────────────
if "token" not in st.session_state:
    st.session_state.token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_upload" not in st.session_state:
    st.session_state.pending_upload = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# Restaura sessão do cookie quando a página é recarregada.
# _saved_token é None no 1º render (JS ainda carregando) e tem valor no 2º rerun.
if st.session_state.token is None and _saved_token and _saved_token not in ("None", ""):
    try:
        r = requests.get(
            f"{API_URL}/auth/me",
            headers={"Authorization": f"Bearer {_saved_token}"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state.token = _saved_token
            st.session_state.user_info = {
                "id": data["id"],
                "name": data["name"],
                "role": data["role"]
            }
        else:
            # Token expirado — remove o cookie silenciosamente
            cookie_manager.remove("omnidoc_token")
    except Exception:
        pass  # Backend offline — mantém o cookie para tentar de novo depois


# ─────────────────────────────────────────────
# Funções Auxiliares
# ─────────────────────────────────────────────
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(endpoint: str, **kwargs):
    try:
        r = requests.post(f"{API_URL}{endpoint}", headers=get_headers(), **kwargs)
        return r
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. O servidor FastAPI está rodando?")
        return None


def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers=get_headers())
        return r
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None


def api_delete(endpoint: str):
    try:
        r = requests.delete(f"{API_URL}{endpoint}", headers=get_headers())
        return r
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None


def do_login(email: str, password: str):
    try:
        r = requests.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": password}
        )
        if r.status_code == 200:
            data = r.json()
            st.session_state.token = data["access_token"]
            st.session_state.user_info = {
                "id": data["user_id"],
                "name": data["name"],
                "role": data["role"]
            }
            st.session_state.messages = []
            # Força recarga do histórico na próxima renderização
            st.session_state.history_loaded = False
            # Salva o token no cookie.
            # IMPORTANTE: NÃO chamar st.rerun() aqui — o rerun interromperia
            # o render antes do JavaScript do cookie_manager executar,
            # fazendo o cookie nunca ser salvo.
            # O roteador no final do script já lida com a troca de página.
            cookie_manager.set("omnidoc_token", data["access_token"])
        else:
            st.error(r.json().get("detail", "Erro no login."))
    except Exception as e:
        st.error(f"Erro de conexão: {e}")


def do_register(name: str, email: str, password: str):
    try:
        r = requests.post(
            f"{API_URL}/auth/register",
            json={"name": name, "email": email, "password": password}
        )
        if r.status_code == 201:
            data = r.json()
            st.success(f"✅ Conta criada! Role: **{data['role']}**. Faça login para continuar.")
        else:
            st.error(r.json().get("detail", "Erro no cadastro."))
    except Exception as e:
        st.error(f"Erro de conexão: {e}")


def upload_document(file, scope: str) -> bool:
    """Faz upload de um PDF e retorna True se bem-sucedido."""
    endpoint = "/documents/upload/company" if scope == "company" else "/documents/upload/personal"
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    r = api_post(endpoint, files=files)
    if r is None:
        return False
    if r.status_code == 200:
        return True
    else:
        st.error(f"Erro no upload: {r.json().get('detail', r.text)}")
        return False


# ─────────────────────────────────────────────
# Página de Autenticação (Login / Cadastro)
# ─────────────────────────────────────────────
def show_auth_page():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("✨ OmniDoc AI")
        st.caption("Assistente inteligente de documentos corporativos.")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Conta"])

        with tab_login:
            with st.form("form_login"):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
                if submitted:
                    if email and password:
                        do_login(email, password)
                    else:
                        st.warning("Preencha e-mail e senha.")

        with tab_register:
            st.caption("O primeiro usuário cadastrado se torna **Admin** automaticamente.")
            with st.form("form_register"):
                name = st.text_input("Nome completo", placeholder="João Silva")
                email_r = st.text_input("E-mail", placeholder="seu@email.com")
                password_r = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres")
                submitted_r = st.form_submit_button("Criar Conta", use_container_width=True, type="primary")
                if submitted_r:
                    if name and email_r and password_r:
                        do_register(name, email_r, password_r)
                    else:
                        st.warning("Preencha todos os campos.")


# ─────────────────────────────────────────────
# Página Principal (Chat)
# ─────────────────────────────────────────────
def show_main_page():
    user = st.session_state.user_info
    is_admin = user["role"] == "admin"

    # ── Restaura histórico da conversa do banco (uma vez por sessão) ──
    if not st.session_state.history_loaded:
        try:
            r = api_get("/chat/history?limit=50")
            if r is not None and r.status_code == 200:
                st.session_state.messages = []
                for item in r.json():
                    st.session_state.messages.append({"role": "user", "content": item["query"]})
                    st.session_state.messages.append({"role": "assistant", "content": item["response"]})
        except Exception:
            pass  # falha silenciosa — não impede o uso do chat
        st.session_state.history_loaded = True

    # ── Sidebar ──────────────────────────────
    with st.sidebar:
        st.title("✨ OmniDoc AI")

        # Info do usuário
        role_html = (
            '<span class="role-badge-admin">ADMIN</span>'
            if is_admin else
            '<span class="role-badge-user">USER</span>'
        )
        st.markdown(f"**{user['name']}** {role_html}", unsafe_allow_html=True)
        st.caption(f"ID: {user['id']}")

        if st.button("🚪 Sair", use_container_width=True):
            cookie_manager.remove("omnidoc_token")
            st.session_state.token = None
            st.session_state.user_info = None
            st.session_state.messages = []
            st.session_state.history_loaded = False
            st.rerun()

        st.divider()

        # ── Painel do ADMIN ──────────────────
        if is_admin:
            st.subheader("🏢 Base da Empresa")
            st.caption("Documentos acessíveis por TODOS os usuários.")

            company_file = st.file_uploader(
                "Adicionar documento corporativo",
                type=["pdf"],
                key="sidebar_company_upload"
            )
            if st.button("📤 Indexar na Base", type="primary", use_container_width=True,
                         disabled=company_file is None):
                with st.spinner("Processando PDF corporativo..."):
                    if upload_document(company_file, "company"):
                        st.success("✅ Documento adicionado à base da empresa!")
                        st.rerun()

            # Lista documentos da empresa
            r = api_get("/documents/company")
            if r and r.status_code == 200:
                docs = r.json()
                if docs:
                    with st.expander(f"📄 {len(docs)} documento(s) corporativo(s)"):
                        for d in docs:
                            col_a, col_b = st.columns([4, 1])
                            with col_a:
                                st.caption(f"#{d['id']} {d['filename']}")
                            with col_b:
                                if st.button("🗑️", key=f"del_company_{d['id']}",
                                             help="Remover documento"):
                                    api_delete(f"/documents/{d['id']}")
                                    st.rerun()

        # ── Painel do Usuário (documentos pessoais) ──
        st.subheader("📁 Meus Documentos")
        st.caption("Visíveis apenas para você.")

        r_personal = api_get("/documents/personal")
        if r_personal and r_personal.status_code == 200:
            personal_docs = r_personal.json()
            if personal_docs:
                with st.expander(f"📄 {len(personal_docs)} documento(s) pessoal(is)"):
                    for d in personal_docs:
                        st.caption(f"#{d['id']} {d['filename']}")
            else:
                st.caption("Nenhum documento pessoal ainda.")

    # ── Área Principal (Chat) ────────────────
    st.title("Como posso ajudar com seus documentos hoje?")

    if is_admin:
        st.info(
            "🏢 Como **Admin**, você pode adicionar documentos à base da empresa pelo painel lateral. "
            "Todos os usuários terão acesso a esses documentos automaticamente.",
            icon="ℹ️"
        )
    else:
        st.info(
            "💡 Você tem acesso à **base de documentos da empresa** automaticamente. "
            "Também pode anexar um PDF pessoal diretamente no campo abaixo para consultas específicas.",
            icon="ℹ️"
        )

    # Exibe histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ── Botão de clipe (posicionado via CSS sobre o chat input) ──
    attached_file = st.file_uploader(
        label="Anexar PDF",
        type=["pdf"],
        label_visibility="collapsed",
        key=f"chat_file_uploader_{st.session_state.uploader_key}",
    )

    # Chip flutuante quando há arquivo selecionado
    if attached_file is not None:
        chip_col, x_col = st.columns([10, 1])
        with chip_col:
            st.markdown(
                f'<div class="file-chip-bar">📎 <b>{attached_file.name}</b>'
                f'<span style="opacity:.6; font-size:11px"> — será indexado ao enviar</span></div>',
                unsafe_allow_html=True
            )
        with x_col:
            if st.button("✕", key="btn_clear_file", help="Remover arquivo"):
                st.session_state.uploader_key += 1
                st.rerun()

    # Campo de chat (fixo no fundo)
    prompt = st.chat_input("Faça uma pergunta sobre os documentos...")

    if prompt:
        # 1. Se há arquivo anexado, faz upload como documento pessoal primeiro
        if attached_file:
            with st.spinner(f"Indexando '{attached_file.name}'... (PDFs grandes podem demorar devido ao rate limit da API)"):
                success = upload_document(attached_file, "personal")
            if success:
                st.toast(f"✅ '{attached_file.name}' indexado com sucesso!", icon="📄")
                # Limpa o uploader após indexar com sucesso
                st.session_state.uploader_key += 1
            else:
                st.stop()

        # 2. Exibe a mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 3. Consulta a IA (RAG multi-escopo automático)
        with st.chat_message("assistant"):
            with st.spinner("Consultando documentos e pensando..."):
                r = api_post("/chat/", json={"query": prompt})

            if r is None:
                st.stop()

            if r.status_code == 200:
                answer = r.json()["response"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                detail = r.json().get("detail", "Erro desconhecido.")
                st.error(f"Erro da API: {detail}")


# ─────────────────────────────────────────────
# Roteador de Páginas
# ─────────────────────────────────────────────
if st.session_state.token is None:
    show_auth_page()
else:
    show_main_page()
