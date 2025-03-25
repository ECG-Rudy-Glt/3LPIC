/**
 * @author GAULT Rudy
 * @company Cloud Temple
 * @created_at 2025-03-25 13:31:07
 * @updated_by GAULT Rudy
 * @updated_at 2025-03-25 14:10:25
 */

// Configuration du mode démo (à désactiver une fois le backend implémenté)
const DEMO_MODE = true;

// Données de démo pour simuler le backend
const demoData = {
  user: {
    id: "demo123",
    email: "demo@coursero.com",
    fullName: "Utilisateur Démo",
  },
  courses: [
    { id: "course1", name: "Algorithmes et structures de données" },
    { id: "course2", name: "Programmation système" },
  ],
  exercises: {
    course1: [
      { id: "ex1", number: 1, name: "Tri à bulle" },
      { id: "ex2", number: 2, name: "Liste chaînée" },
      { id: "ex3", number: 3, name: "Arbre binaire" },
    ],
    course2: [
      { id: "ex4", number: 1, name: "Gestion de processus" },
      { id: "ex5", number: 2, name: "Threads" },
      { id: "ex6", number: 3, name: "Sockets" },
    ],
  },
  submissions: [
    {
      id: "sub1",
      courseName: "Algorithmes et structures de données",
      exerciseName: "Exercice 1 - Tri à bulle",
      language: "python",
      status: "completed",
      score: 85,
    },
    {
      id: "sub2",
      courseName: "Programmation système",
      exerciseName: "Exercice 2 - Threads",
      language: "c",
      status: "pending",
    },
  ],
};

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
    if (DEMO_MODE) {
      // Mode démo: accepter n'importe quel email/mot de passe
      const demoToken = "demo_token_" + Math.random().toString(36).substring(2);
      localStorage.setItem("token", demoToken);
      localStorage.setItem("user", JSON.stringify(demoData.user));

      appState.isAuthenticated = true;
      appState.user = demoData.user;

      updateUIState();
      loadAvailableCourses();
      showNotification("Connexion réussie (mode démo)", "success");
      return;
    }

    // Appel à l'API d'authentification (mode normal)
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
    if (DEMO_MODE) {
      // Mode démo: utiliser les données fictives
      appState.availableCourses = demoData.courses;

      // Mettre à jour le menu déroulant des cours si disponible
      const courseSelect = document.getElementById("course");
      if (courseSelect) {
        courseSelect.innerHTML =
          `<option value="">Sélectionnez un cours</option>` +
          demoData.courses
            .map(
              (course) => `<option value="${course.id}">${course.name}</option>`
            )
            .join("");
      }
      return;
    }

    // Mode normal: appel à l'API
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
    if (DEMO_MODE) {
      // Mode démo: utiliser les données fictives
      const exercises = demoData.exercises[courseId] || [];
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
      return;
    }

    // Mode normal: appel à l'API
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
    if (DEMO_MODE) {
      // Mode démo: utiliser les données fictives
      appState.submissions = demoData.submissions;
      updateSubmissionsTable();
      return;
    }

    // Mode normal: appel à l'API
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

    if (DEMO_MODE) {
      // Simuler un délai d'envoi en mode démo
      progressBar.style.width = "50%";
      await new Promise((resolve) => setTimeout(resolve, 1000));
      progressBar.style.width = "100%";

      // Ajouter une soumission fictive
      const courseName =
        demoData.courses.find((c) => c.id === courseId)?.name || courseId;
      const exercise = demoData.exercises[courseId]?.find(
        (e) => e.id === exerciseId
      );
      const exerciseName = exercise
        ? `Exercice ${exercise.number} - ${exercise.name}`
        : exerciseId;

      demoData.submissions.unshift({
        id: "sub_" + Math.random().toString(36).substring(2),
        courseName: courseName,
        exerciseName: exerciseName,
        language: language,
        status: "pending",
      });

      statusMessage.textContent =
        "Soumission réussie! Votre code est en attente d'évaluation.";
      showNotification("Fichier envoyé avec succès (mode démo)", "success");

      // Rediriger vers le tableau de bord après un court délai
      setTimeout(() => {
        window.location.href = "authentication.html";
      }, 2000);
      return;
    }

    // Créer un objet FormData pour l'envoi du fichier (mode normal)
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

  if (!submissionsTable) return;

  if (!appState.submissions.length) {
    submissionsTable.innerHTML = `<tr><td colspan="5" class="text-center">Aucune soumission trouvée</td></tr>`;
    return;
  }

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

// Fonction pour simuler l'évaluation en mode démo
function setupDemoEvaluation() {
  if (!DEMO_MODE) return;

  // Vérifier périodiquement s'il y a des soumissions en attente, puis les évaluer
  setInterval(() => {
    const pendingSubmissions = demoData.submissions.filter(
      (sub) => sub.status === "pending"
    );

    for (const sub of pendingSubmissions) {
      // Simuler un statut "en cours d'évaluation" pendant quelques secondes
      sub.status = "processing";

      // Simuler la fin de l'évaluation avec un score aléatoire
      setTimeout(() => {
        sub.status = "completed";
        sub.score = Math.floor(Math.random() * 40) + 60; // Score entre 60 et 100
        updateSubmissionsTable();
      }, 5000);
    }

    if (pendingSubmissions.length > 0) {
      updateSubmissionsTable();
    }
  }, 3000);
}

// Démarrer la simulation d'évaluation en mode démo
setupDemoEvaluation();
