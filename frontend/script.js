/**
 * @author GAULT Rudy
 * @company Cloud Temple
 * @created_at 2025-03-25 13:31:07
 * @updated_by GAULT Rudy
 * @updated_at 2025-03-25 13:56:52
 */

// Gestion de l'état de l'application
const appState = {
  isAuthenticated: false,
  user: null,
  submissions: [],
  availableCourses: [],
  availableExercises: {},
};

// Configuration de l'API
const API = {
  BASE_URL: "/api", // Remplacer par l'URL réelle de l'API
  ENDPOINTS: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    SUBMISSIONS: "/submissions",
    COURSES: "/courses",
    EXERCISES: "/exercises",
    SUBMIT: "/submit",
  },
};

// Fonction d'initialisation
document.addEventListener("DOMContentLoaded", () => {
  checkAuthState();
  setupEventListeners();
  if (appState.isAuthenticated) {
    loadAvailableCourses();
  }
});

// Vérification de l'état d'authentification
function checkAuthState() {
  const token = localStorage.getItem("token");
  const user = localStorage.getItem("user");

  if (token && user) {
    appState.isAuthenticated = true;
    appState.user = JSON.parse(user);
    updateUIState();
    fetchUserSubmissions(); // Charger les soumissions réelles de l'utilisateur
  }
}

// Configuration des écouteurs d'événements
function setupEventListeners() {
  const loginForm = document.getElementById("login-form");
  const logoutButton = document.getElementById("logout");
  const uploadForm = document.getElementById("upload-form");
  const courseSelect = document.getElementById("course");

  if (loginForm) {
    loginForm.addEventListener("submit", handleLogin);
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", handleLogout);
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", handleUpload);
    setupFileValidation();
  }

  // Ajouter un écouteur pour mettre à jour les exercices disponibles lorsqu'un cours est sélectionné
  if (courseSelect) {
    courseSelect.addEventListener("change", function () {
      loadExercisesForCourse(this.value);
    });
  }
}

// Gestion de la connexion
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    // Appel à l'API d'authentification
    const response = await fetch(`${API.BASE_URL}${API.ENDPOINTS.LOGIN}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error("Identifiants incorrects");
    }

    const data = await response.json();

    // Enregistrer le token et les infos utilisateur
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));

    appState.isAuthenticated = true;
    appState.user = data.user;

    updateUIState();
    loadAvailableCourses();
    showNotification("Connexion réussie", "success");
  } catch (error) {
    showNotification(error.message, "error");
  }
}

// Gestion de la déconnexion
function handleLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  appState.isAuthenticated = false;
  appState.user = null;
  appState.submissions = [];
  updateUIState();
  showNotification("Déconnexion réussie", "success");
}

// Chargement des cours disponibles
async function loadAvailableCourses() {
  try {
    const response = await fetch(`${API.BASE_URL}${API.ENDPOINTS.COURSES}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (!response.ok) throw new Error("Impossible de charger les cours");

    const courses = await response.json();
    appState.availableCourses = courses;

    // Mettre à jour le menu déroulant des cours si disponible
    const courseSelect = document.getElementById("course");
    if (courseSelect) {
      courseSelect.innerHTML =
        `<option value="">Sélectionnez un cours</option>` +
        courses
          .map(
            (course) => `<option value="${course.id}">${course.name}</option>`
          )
          .join("");
    }
  } catch (error) {
    console.error("Erreur lors du chargement des cours:", error);
    showNotification("Impossible de charger les cours", "error");
  }
}

// Chargement des exercices pour un cours spécifique
async function loadExercisesForCourse(courseId) {
  if (!courseId) return;

  try {
    const response = await fetch(
      `${API.BASE_URL}${API.ENDPOINTS.EXERCISES}?courseId=${courseId}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) throw new Error("Impossible de charger les exercices");

    const exercises = await response.json();
    appState.availableExercises[courseId] = exercises;

    // Mettre à jour le menu déroulant des exercices
    const exerciseSelect = document.getElementById("exercise");
    if (exerciseSelect) {
      exerciseSelect.innerHTML =
        `<option value="">Sélectionnez un exercice</option>` +
        exercises
          .map(
            (ex) =>
              `<option value="${ex.id}">Exercice ${ex.number} - ${ex.name}</option>`
          )
          .join("");
    }
  } catch (error) {
    console.error("Erreur lors du chargement des exercices:", error);
    showNotification("Impossible de charger les exercices", "error");
  }
}

// Récupération des soumissions de l'utilisateur
async function fetchUserSubmissions() {
  try {
    const response = await fetch(
      `${API.BASE_URL}${API.ENDPOINTS.SUBMISSIONS}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) throw new Error("Impossible de charger les soumissions");

    const data = await response.json();
    appState.submissions = data.submissions;

    updateSubmissionsTable();
  } catch (error) {
    console.error("Erreur lors du chargement des soumissions:", error);
  }
}

// Gestion de l'upload de fichier
async function handleUpload(e) {
  e.preventDefault();

  const courseId = document.getElementById("course").value;
  const exerciseId = document.getElementById("exercise").value;
  const language = document.getElementById("language").value;
  const file = document.getElementById("code-file").files[0];

  if (!courseId || !exerciseId || !language || !file) {
    showNotification("Veuillez remplir tous les champs", "error");
    return;
  }

  if (!validateFile(file, language)) {
    showNotification("Format de fichier invalide", "error");
    return;
  }

  try {
    const uploadStatus = document.getElementById("upload-status");
    const progressBar = uploadStatus.querySelector(".progress");
    const statusMessage = uploadStatus.querySelector(".status-message");

    uploadStatus.classList.remove("hidden");
    statusMessage.textContent = "Envoi en cours...";
    progressBar.style.width = "25%";

    // Créer un objet FormData pour l'envoi du fichier
    const formData = new FormData();
    formData.append("file", file);
    formData.append("courseId", courseId);
    formData.append("exerciseId", exerciseId);
    formData.append("language", language);

    // Envoyer le fichier au serveur
    const response = await fetch(`${API.BASE_URL}${API.ENDPOINTS.SUBMIT}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: formData,
    });

    progressBar.style.width = "100%";

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Erreur lors de l'envoi du fichier");
    }

    const result = await response.json();

    statusMessage.textContent =
      "Soumission réussie! Votre code est en attente d'évaluation.";
    showNotification("Fichier envoyé avec succès", "success");

    // Rediriger vers le tableau de bord après un court délai
    setTimeout(() => {
      window.location.href = "authentication.html";
    }, 2000);
  } catch (error) {
    showNotification(error.message, "error");
  }
}

// Validation du fichier
function validateFile(file, language) {
  if (!file) return false;

  const allowedExtensions = {
    python: ".py",
    c: ".c",
  };

  const fileExtension = file.name
    .toLowerCase()
    .slice(file.name.lastIndexOf("."));
  return fileExtension === allowedExtensions[language];
}

// Configuration de la validation des fichiers
function setupFileValidation() {
  const fileInput = document.getElementById("code-file");
  const languageSelect = document.getElementById("language");

  if (fileInput && languageSelect) {
    languageSelect.addEventListener("change", () => {
      const language = languageSelect.value;
      fileInput.accept = language === "python" ? ".py" : ".c";
    });
  }
}

// Mise à jour de l'interface utilisateur
function updateUIState() {
  const authSection = document.getElementById("auth-section");
  const dashboard = document.getElementById("dashboard");

  if (appState.isAuthenticated) {
    if (authSection) authSection.classList.add("hidden");
    if (dashboard) dashboard.classList.remove("hidden");
  } else {
    if (authSection) authSection.classList.remove("hidden");
    if (dashboard) dashboard.classList.add("hidden");
  }
}

// Mise à jour du tableau des soumissions
function updateSubmissionsTable() {
  const submissionsTable = document.getElementById("submissions-table");

  if (!submissionsTable || !appState.submissions.length) return;

  submissionsTable.innerHTML = appState.submissions
    .map((sub) => {
      let statusClass = "";
      let scoreDisplay = "-";

      // Appliquer des styles en fonction du statut
      if (sub.status === "completed") {
        statusClass = "success";
        scoreDisplay = `${sub.score}%`;
      } else if (sub.status === "error") {
        statusClass = "error";
      }

      return `
        <tr>
          <td>${sub.courseName}</td>
          <td>${sub.exerciseName}</td>
          <td>${sub.language}</td>
          <td class="${statusClass}">${translateStatus(sub.status)}</td>
          <td>${scoreDisplay}</td>
        </tr>
      `;
    })
    .join("");
}

// Traduction des statuts en français
function translateStatus(status) {
  const statusMap = {
    pending: "En attente",
    processing: "En cours d'évaluation",
    completed: "Évalué",
    error: "Erreur",
  };

  return statusMap[status] || status;
}

// Affichage des notifications
function showNotification(message, type) {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// Fonction de rafraîchissement périodique des soumissions
function setupSubmissionsPolling() {
  if (appState.isAuthenticated) {
    // Vérifier les nouvelles soumissions toutes les 30 secondes
    setInterval(fetchUserSubmissions, 30000);
  }
}
