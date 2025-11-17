import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  signInAnonymously
} from "https://www.gstatic.com/firebasejs/10.12.4/firebase-auth.js";
import {
  addDoc,
  collection,
  getFirestore,
  onSnapshot,
  orderBy,
  query,
  serverTimestamp,
  where
} from "https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js";

/* =========================
   1) Config de Firebase
========================= */
const firebaseConfig = {
  apiKey: "AIzaSyA5MvL1YMfWM4uScgHtF_XNl7kHAKbP0Aw",
  authDomain: "chatbot-faq-e290d.firebaseapp.com",
  projectId: "chatbot-faq-e290d",
  storageBucket: "chatbot-faq-e290d.firebasestorage.app",
  messagingSenderId: "754778077037",
  appId: "1:754778077037:web:75dd3412810ff75a410c64",
  measurementId: "G-2MEFJ6F22G"
};

const app  = initializeApp(firebaseConfig);
const db   = getFirestore(app);
const auth = getAuth(app);

/* =========================
   2) Referencias de UI
========================= */
const faqListEl     = document.getElementById('faqList');
const faqDetailEl   = document.getElementById('faqDetail');
const faqQEl        = document.getElementById('faqQuestion');
const faqAEl        = document.getElementById('faqAnswer');
const faqTagsEl     = document.getElementById('faqTags');
const btnSearch     = document.getElementById('btnSearch');
const searchInput   = document.getElementById('searchInput');
const tagInput      = document.getElementById('tagInput');
const statusEl      = document.getElementById('status');
const btnUseful     = document.getElementById('btnUseful');
const btnNotUseful  = document.getElementById('btnNotUseful');
const btnFeedback   = document.getElementById('btnSendFeedback');
const txtComment    = document.getElementById('txtComment');

/* =========================
   3) Estado
========================= */
let currentFAQ = null;
let currentInteractionId = null;
let unsubscribeFaqs = null;     // ← guarda la suscripción activa
let authReady = false;          // ← evita doble carga por onAuthStateChanged

/* =========================
   4) Autenticación anónima
========================= */
onAuthStateChanged(auth, async (user) => {
  try {
    if (!user) {
      await signInAnonymously(auth);
      return; // esperamos al siguiente onAuthStateChanged con user
    }
    if (authReady) return;  // ya nos autenticamos y suscribimos
    authReady = true;

    // Suscripción inicial sin filtros
    subscribeFAQs({ qText: "", tag: "" });
  } catch (err) {
    console.error("Auth error:", err);
  }
});

/* ===========================================================
   5) Suscripción a FAQs con filtros (sin duplicados)
=========================================================== */
function subscribeFAQs({ qText = "", tag = "" } = {}) {
  // Si ya hay una suscripción activa, la cancelamos
  if (typeof unsubscribeFaqs === "function") {
    unsubscribeFaqs();
    unsubscribeFaqs = null;
  }

  // Construimos la query base: solo activas
  let qRef = query(
    collection(db, "faqs"),
    where("active", "==", true),
    orderBy("question")
  );

  // Filtro por etiqueta (server-side)
  const tagTrim = (tag || "").trim().toLowerCase();
  if (tagTrim) {
    qRef = query(
      collection(db, "faqs"),
      where("active", "==", true),
      where("tags", "array-contains", tagTrim),
      orderBy("question")
    );
  }

  statusEl.textContent = "Cargando...";

  // Nueva suscripción
  unsubscribeFaqs = onSnapshot(qRef, (snap) => {
    // Mapeamos docs
    let faqs = snap.docs.map(d => ({ id: d.id, ...d.data() }));

    // Filtro de texto (client-side)
    const qLower = (qText || "").toLowerCase();
    if (qLower) {
      faqs = faqs.filter(f =>
        (f.question || "").toLowerCase().includes(qLower) ||
        (f.answer   || "").toLowerCase().includes(qLower)
      );
    }

    // Deduplicar por ID (por seguridad)
    faqs = Array.from(new Map(faqs.map(f => [f.id, f])).values());

    // Render
    renderFaqList(faqs);
    statusEl.textContent = `Mostrando ${faqs.length} FAQ(s)`;
  }, (err) => {
    console.error("onSnapshot error:", err);
    statusEl.textContent = "Error cargando FAQs";
  });
}

/* =========================
   6) Render de la lista
========================= */
function renderFaqList(faqs) {
  faqListEl.innerHTML = "";  // ← limpia SIEMPRE antes de pintar

  if (!faqs.length) {
    faqListEl.innerHTML = `<li>No hay resultados</li>`;
    return;
  }

  faqs.forEach(f => {
    const li = document.createElement('li');
    li.innerHTML = `
      <strong>${escapeHtml(f.question)}</strong><br/>
      <small>tags: ${(f.tags || []).join(', ')}</small>
    `;
    li.addEventListener('click', () => openFAQ(f));
    faqListEl.appendChild(li);
  });
}

/* ==============================================
   7) Abrir detalle + registrar interacción
============================================== */
async function openFAQ(faq) {
  currentFAQ = faq;
  faqQEl.textContent   = faq.question || '';
  faqAEl.textContent   = faq.answer || '';
  faqTagsEl.textContent= `Etiquetas: ${(faq.tags || []).join(', ')}`;
  faqDetailEl.classList.remove('hidden');

  try {
    const docRef = await addDoc(collection(db, 'interactions'), {
      userId: auth.currentUser?.uid || null,
      query: faq.question || '',
      answerId: faq.id,
      latencyMs: 0,
      createdAt: serverTimestamp()
    });
    currentInteractionId = docRef.id;
  } catch (err) {
    console.warn('No se pudo registrar la interacción:', err.message);
    currentInteractionId = null;
  }
}

/* =========================
   8) Feedback
========================= */
btnFeedback.addEventListener('click', async () => {
  if (!currentFAQ) return alert("Primero selecciona una FAQ.");

  const useful = btnUseful.dataset.active === '1'
               ? true
               : btnNotUseful.dataset.active === '1'
                 ? false
                 : null;
  if (useful === null) return alert("Selecciona si fue útil (👍) o no (👎).");

  try {
    await addDoc(collection(db, 'feedback'), {
      interactionId: currentInteractionId || null,
      useful,
      comment: (txtComment.value || '').trim(),
      createdAt: serverTimestamp()
    });
    alert("¡Gracias por tu feedback!");
    btnUseful.dataset.active   = '0';
    btnNotUseful.dataset.active= '0';
    txtComment.value = '';
  } catch (err) {
    alert("Error enviando feedback: " + err.message);
  }
});

// Toggle útil / no útil
btnUseful.addEventListener('click', () => {
  btnUseful.dataset.active   = btnUseful.dataset.active === '1' ? '0' : '1';
  btnNotUseful.dataset.active= '0';
});
btnNotUseful.addEventListener('click', () => {
  btnNotUseful.dataset.active= btnNotUseful.dataset.active === '1' ? '0' : '1';
  btnUseful.dataset.active   = '0';
});

/* =========================
   9) Búsqueda / Filtros
========================= */
btnSearch.addEventListener('click', () => {
  subscribeFAQs({ qText: searchInput.value, tag: tagInput.value });
});

/* =========================
   10) Utilidad: escapar HTML
========================= */
function escapeHtml(str = "") {
  return str.replace(/[&<>"']/g, s => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[s]));
}


// =================================================================
//  🔥 NUEVA SECCIÓN: CRUD de USUARIOS con FastAPI (secciones separadas)
// =================================================================

// --- Configuración del backend (FastAPI) ---
const API_BASE_URL = "http://127.0.0.1:8000";  // Ajusta según tu entorno

async function callFastAPI(endpoint, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE_URL}${endpoint}`, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  if (res.status === 204) return null;
  return await res.json();
}

// ==========================================================
// ➕ CREAR USUARIO
// ==========================================================
const btnCreateUser   = document.getElementById("btnCreateUser");
const inputCreateName = document.getElementById("createUserName");
const inputCreateMail = document.getElementById("createUserEmail");
const statusCreate    = document.getElementById("statusCreate");
const outputCreate    = document.getElementById("outputCreate");

btnCreateUser.addEventListener("click", async () => {
  const name  = inputCreateName.value.trim();
  const email = inputCreateMail.value.trim();
  if (!name || !email) return alert("Completa nombre y correo");

  statusCreate.textContent = "Creando usuario...";
  outputCreate.innerHTML = "";
  try {
    const data = await callFastAPI("/users/", "POST", { userName: name, userEmail: email });
    statusCreate.textContent = "✅ Usuario creado correctamente";
    outputCreate.innerHTML = renderUser(data);
  } catch (err) {
    statusCreate.textContent = `❌ Error: ${err.message}`;
  }
});

// ==========================================================
// 🔍 OBTENER USUARIO POR ID
// ==========================================================
const btnFetchUser = document.getElementById("btnFetchUser");
const inputFetchId = document.getElementById("fetchUserId");
const statusFetch  = document.getElementById("statusFetch");
const outputFetch  = document.getElementById("outputFetch");

btnFetchUser.addEventListener("click", async () => {
  const id = inputFetchId.value.trim();
  if (!id) return alert("Escribe un ID");

  statusFetch.textContent = "Buscando usuario...";
  outputFetch.innerHTML = "";
  try {
    const data = await callFastAPI(`/users/${id}`);
    statusFetch.textContent = "✅ Usuario encontrado";
    outputFetch.innerHTML = renderUser(data);
  } catch (err) {
    statusFetch.textContent = `❌ Error: ${err.message}`;
  }
});

// ==========================================================
// ✏️ ACTUALIZAR USUARIO
// ==========================================================
const btnUpdateUser   = document.getElementById("btnUpdateUser");
const inputUpdateId   = document.getElementById("updateUserId");
const inputUpdateName = document.getElementById("updateUserName");
const inputUpdateMail = document.getElementById("updateUserEmail");
const statusUpdate    = document.getElementById("statusUpdate");
const outputUpdate    = document.getElementById("outputUpdate");

btnUpdateUser.addEventListener("click", async () => {
  const id = inputUpdateId.value.trim();
  const name  = inputUpdateName.value.trim();
  const email = inputUpdateMail.value.trim();
  if (!id) return alert("ID requerido");

  statusUpdate.textContent = "Actualizando usuario...";
  outputUpdate.innerHTML = "";
  try {
    const data = await callFastAPI(`/users/${id}`, "PUT", { userName: name, userEmail: email });
    statusUpdate.textContent = "✅ Usuario actualizado";
    outputUpdate.innerHTML = renderUser(data);
  } catch (err) {
    statusUpdate.textContent = `❌ Error: ${err.message}`;
  }
});

// ==========================================================
// 🗑️ ELIMINAR USUARIO
// ==========================================================
const btnDeleteUser = document.getElementById("btnDeleteUser");
const inputDeleteId = document.getElementById("deleteUserId");
const statusDelete  = document.getElementById("statusDelete");
const outputDelete  = document.getElementById("outputDelete");

btnDeleteUser.addEventListener("click", async () => {
  const id = inputDeleteId.value.trim();
  if (!id) return alert("Escribe un ID");
  if (!confirm("¿Seguro que deseas eliminarlo?")) return;

  statusDelete.textContent = "Eliminando usuario...";
  outputDelete.innerHTML = "";
  try {
    await callFastAPI(`/users/${id}`, "DELETE");
    statusDelete.textContent = "🗑️ Usuario eliminado correctamente";
  } catch (err) {
    statusDelete.textContent = `❌ Error: ${err.message}`;
  }
});

// ==========================================================
// 📋 LISTAR USUARIOS
// ==========================================================
const btnListUsers = document.getElementById("btnListUsers");
const statusList   = document.getElementById("statusList");
const outputList   = document.getElementById("outputList");

btnListUsers.addEventListener("click", async () => {
  statusList.textContent = "Cargando lista...";
  outputList.innerHTML = "";
  try {
    const users = await callFastAPI("/users/");
    statusList.textContent = `✅ ${users.length} usuarios encontrados`;
    outputList.innerHTML = renderUserList(users);
  } catch (err) {
    statusList.textContent = `❌ Error: ${err.message}`;
  }
});

// ==========================================================
// 📘 CONSULTAR RAG
// ==========================================================
const btnAskRag  = document.getElementById("btnAskRag");
const ragInput   = document.getElementById("ragInput");
const statusRag  = document.getElementById("statusRag");
const outputRag  = document.getElementById("outputRag");

btnAskRag.addEventListener("click", async () => {
  const question = ragInput.value.trim();

  if (!question) {
    statusRag.textContent = "⚠️ Escribe una pregunta.";
    return;
  }

  statusRag.textContent = "🔄 Consultando RAG...";
  outputRag.innerHTML = "";

  try {
    // ✔️ Llamada correcta al endpoint FastAPI
    const response = await callFastAPI(
      "/rag/generate_answer",
      "POST",
      { question: question }
    );

    // Tu endpoint regresa: { llm_generated_answer: "texto..." }
    const markdownText = response.llm_generated_answer;

    const renderedHtml = marked.parse(markdownText);

    statusRag.textContent = "✅ Respuesta recibida";
    outputRag.innerHTML = `<div class="markdown">${renderedHtml}</div>`;

  } catch (err) {
    statusRag.textContent = `❌ Error: ${err.message}`;
  }
});


// ==========================================================
// 🧩 FUNCIONES DE RENDERIZADO
// ==========================================================
function renderUser(user) {
  return `
    <div class="card">
      <h4>${escapeHtml(user.userName)}</h4>
      <p>Email: ${escapeHtml(user.userEmail)}</p>
      <small>ID: ${escapeHtml(user.userId)}</small>
    </div>
  `;
}

function renderUserList(users) {
  if (!users.length) return "<p>No hay usuarios registrados.</p>";
  return users.map(u => renderUser(u)).join("");
}
