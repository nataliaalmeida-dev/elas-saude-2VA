/* ============================================================
   UTIL
============================================================ */
const $ = (sel) => document.querySelector(sel);


/* Profissionais (Injetados via Jinja no HTML) */
const PROFISSIONAIS = window.PROFISSIONAIS_DB || [];


/* ============================================================
   LISTAGEM DE PROFISSIONAIS
============================================================ */
const resultsContainer = $("#results");
const searchInput = $("#searchInput");
const specialtySelect = $("#specialtySelect");
const searchBtn = $("#searchBtn");

function listarEspecialidades() {
  if (!specialtySelect) return;

  const lista = [...new Set(PROFISSIONAIS.map((p) => p.especialidade))];
  specialtySelect.innerHTML = '<option value="">Todas as especialidades</option>';

  lista.forEach((esp) => {
    const op = document.createElement("option");
    op.value = esp;
    op.textContent = esp;
    specialtySelect.appendChild(op);
  });
}

function renderResults(data) {
  if (!resultsContainer) return;

  resultsContainer.innerHTML = "";

  if (data.length === 0) {
    resultsContainer.innerHTML = '<p class="muted">Nenhum profissional encontrado.</p>';
    return;
  }

  data.forEach((item) => {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
      <img src="${item.foto}" alt="${item.nome}" onerror="this.src='/static/assets/usuario/usuario.png'">
      <div style="flex:1">
        <h3>${item.nome}</h3>
        <p>${item.especialidade} — CRM: ${item.crm}</p>
      </div>
      <button class="btn schedule" data-id="${item.id}">Agendar</button>
    `;

    card.querySelector(".schedule").addEventListener("click", () => {
      window.location.href = `/agendar?id=${item.id}`;
    });

    resultsContainer.appendChild(card);
  });
}

function atualizarLista() {
  if (!resultsContainer) return;

  let lista = PROFISSIONAIS;
  const busca = searchInput?.value.trim().toLowerCase() || "";
  const esp = specialtySelect?.value || "";

  if (busca) {
    lista = lista.filter((p) =>
      p.nome.toLowerCase().includes(busca) ||
      p.especialidade.toLowerCase().includes(busca)
    );
  }

  if (esp) lista = lista.filter((p) => p.especialidade === esp);

  renderResults(lista);
}

if (resultsContainer) {
  listarEspecialidades();
  atualizarLista();

  searchBtn?.addEventListener("click", atualizarLista);
  searchInput?.addEventListener("input", atualizarLista);
  specialtySelect?.addEventListener("change", atualizarLista);
}

/* ============================================================
   DETECÇÃO DA PÁGINA
============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  const pagina = window.location.pathname.split("/").pop();

  if (pagina === "agendar" || pagina === "agendar.html") {
    iniciarPaginaAgendamento();
  }
});

/* ============================================================
   PÁGINA DE AGENDAMENTO
============================================================ */
function iniciarPaginaAgendamento() {
  const params = new URLSearchParams(window.location.search);
  const profId = params.get("id");

  if (!profId) {
    alert("Profissional não encontrado.");
    window.location.href = "/profissionais";
    return;
  }

  carregarProfissional(profId);
  carregarAgenda(profId);
}

function carregarProfissional(id) {
  const prof = window.PROFISSIONAL_ATUAL;
  if (!prof) return;

  $("#prof-nome").textContent = prof.nome;
  $("#prof-area").textContent = prof.especialidade;
  $("#prof-foto").src = prof.foto || "/static/assets/user.png";
}

/* ============================================================
   AGENDA — DIAS E HORÁRIOS
============================================================ */
function carregarAgenda(profId) {
  const container = document.getElementById("agenda-container");
  container.innerHTML = "";

  const hoje = new Date();
  const dias = 5;

  for (let i = 0; i < dias; i++) {
    const data = new Date();
    data.setDate(hoje.getDate() + i);

    const dataStr = data.toISOString().split("T")[0];
    const titulo = data.toLocaleDateString("pt-BR", {
      weekday: "long",
      day: "numeric",
      month: "short"
    });

    const bloco = document.createElement("div");
    bloco.className = "dia-bloco";

    bloco.innerHTML = `
      <h3>${titulo}</h3>
      <div class="horarios" id="horarios-${dataStr}"></div>
    `;

    container.appendChild(bloco);
    gerarHorarios(dataStr, profId);
  }
}

function gerarHorarios(dataStr, profId) {
  const horariosContainer = document.getElementById(`horarios-${dataStr}`);

  const horarios = ["08:00", "09:00", "10:00", "13:00", "14:00", "15:00", "16:00"];

  const agendamentos = window.AGENDAMENTOS_PROFISSIONAL || [];

  horarios.forEach(hora => {
    const dataCompleta = `${dataStr} ${hora}:00`;

    const ocupado = agendamentos.some(
      a => a.profissional_id == profId && a.data_hora === dataCompleta
    );

    const btn = document.createElement("button");
    btn.className = "hora-btn";
    btn.textContent = hora;

    if (ocupado) {
      btn.classList.add("ocupado");
      btn.disabled = true;
    } else {
      btn.onclick = () => confirmarAgendamento(profId, dataStr, hora);
    }

    horariosContainer.appendChild(btn);
  });
}

/* ============================================================
   CONFIRMAR AGENDAMENTO
============================================================ */
async function confirmarAgendamento(profId, dataStr, hora) {
  const dataHora = `${dataStr} ${hora}:00`;
  const resposta = await fetch("/agendar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profissional_id: profId, data_hora: dataHora })
  });

  if (resposta.ok) {
    alert("Agendamento realizado com sucesso!");
    window.location.href = "/agendamentos";
  } else {
    alert("Erro ao agendar. Faça login novamente.");
    window.location.href = "/";
  }
}
/* ============================================================
   CANCELAR AGENDAMENTO
============================================================ */
document.addEventListener("click", async (e) => {
  if (e.target.classList.contains("cancelar-btn")) {

    const id = Number(e.target.getAttribute("data-id"));

    if (!confirm("Deseja realmente cancelar este agendamento?")) {
      return;
    }

    const resposta = await fetch(`/cancelar_agendamento/${id}`, { method: "POST" });
    if (resposta.ok) {
        alert("Agendamento cancelado com sucesso!");
        window.location.reload();
    } else {
        alert("Erro ao cancelar agendamento.");
    }
  }
});
/* ============================================================
   FORÇAR REFRESH NO VOLTAR (BFCache)
============================================================ */
window.addEventListener("pageshow", function (event) {
  if (event.persisted) {
    window.location.reload();
  }
});

/* ============================================================
   MENU DO USUÁRIO (Apenas abrir/fechar dropdown)
============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  const avatar = document.getElementById("userAvatar");
  const dropdown = document.getElementById("userDropdown");
  const logoutBtn = document.getElementById("logoutBtn");

  if (!avatar || !dropdown) return;

  /* ================================
     1) Abrir/fechar dropdown
  ================================= */
  avatar.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  });

  document.addEventListener("click", () => {
    dropdown.classList.remove("show");
  });

  dropdown.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  /* ================================
     2) Logout
  ================================= */
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      // Em uma aplicação Flask, idealmente redirecionar para uma rota /logout
      window.location.href = "/";
    });
  }
});
