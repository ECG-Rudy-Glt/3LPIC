// Configuration globale
const API_BASE_URL = 'http://192.168.159.233:5000';
let currentUser = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page chargée, initialisation...');

    // Vérification de session
    checkUserSession();

    // Test de connexion à l'API
    testAPIConnection();

    // Attachement des gestionnaires d'événements selon la page
    setupEventHandlers();
});

// Test de connexion à l'API
function testAPIConnection() {
    console.log('Test de connexion à l\'API...');
    fetch(`${API_BASE_URL}/api/health`)
        .then(response => response.json())
        .then(data => console.log('API Health check:', data))
        .catch(error => console.error('Erreur de connexion à l\'API:', error));
}

// Vérification de session utilisateur
function checkUserSession() {
    const userJson = localStorage.getItem('courseroUser');
    if (userJson) {
        try {
            currentUser = JSON.parse(userJson);
            console.log('Session utilisateur trouvée:', currentUser.email);

            // Si on est sur la page d'authentification, afficher le dashboard
            if (document.getElementById('dashboard')) {
                document.getElementById('auth-section').classList.add('hidden');
                document.getElementById('dashboard').classList.remove('hidden');
                loadUserSubmissions();
            }
        } catch (e) {
            console.error('Erreur lors du chargement de la session:', e);
            localStorage.removeItem('courseroUser');
        }
    } else {
        console.log('Aucune session utilisateur trouvée');
    }
}

// Configuration des gestionnaires d'événements selon la page
function setupEventHandlers() {
    // Formulaire de connexion
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        console.log('Formulaire de connexion détecté');
        loginForm.addEventListener('submit', handleLogin);
    }

    // Formulaire d'inscription
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        console.log('Formulaire d\'inscription détecté');
        registerForm.addEventListener('submit', handleRegister);
    }

    // Bouton de déconnexion
    const logoutButton = document.getElementById('logout');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }

    // Formulaire d'upload
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        console.log('Formulaire de soumission détecté');

        // Chargement des cours
        loadCourses();

        // Événement de changement de cours
        const courseSelect = document.getElementById('course');
        if (courseSelect) {
            courseSelect.addEventListener('change', function() {
                loadExercises(this.value);
            });
        }

        // Soumission du formulaire
        uploadForm.addEventListener('submit', handleCodeSubmission);
    }
}

// Gestion de l'inscription
function handleRegister(e) {
    e.preventDefault();
    console.log('Traitement du formulaire d\'inscription...');

    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        alert('Les mots de passe ne correspondent pas!');
        return;
    }

    const formData = {
        email: document.getElementById('email').value,
        password: password,
        full_name: document.getElementById('fullName').value
    };

    console.log('Données d\'inscription:', formData);
    console.log('URL de l\'API:', `${API_BASE_URL}/api/auth/register`);

    fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Inscription réussie:', data);
        alert('Inscription réussie! Vous pouvez maintenant vous connecter.');
        window.location.href = 'authentication.html';
    })
    .catch(error => {
        console.error('Erreur lors de l\'inscription:', error);
        alert('Erreur lors de l\'inscription: ' + error.message);
    });
}

// Gestion de la connexion
function handleLogin(e) {
    e.preventDefault();
    console.log('Traitement du formulaire de connexion...');

    const formData = {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };

    console.log('Données de connexion:', formData);

    fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Connexion réussie:', data);

        // Stockage des infos utilisateur
        currentUser = {
            id: data.user_id,
            email: formData.email
        };
        localStorage.setItem('courseroUser', JSON.stringify(currentUser));

        // Mise à jour de l'interface
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');

        // Chargement des soumissions
        loadUserSubmissions();
    })
    .catch(error => {
        console.error('Erreur lors de la connexion:', error);
        alert('Erreur lors de la connexion: ' + error.message);
    });
}

// Gestion de la déconnexion
function handleLogout() {
    console.log('Déconnexion...');
    localStorage.removeItem('courseroUser');
    currentUser = null;
    window.location.href = 'authentication.html';
}

// Chargement des cours
function loadCourses() {
    console.log('Chargement des cours...');

    fetch(`${API_BASE_URL}/api/courses`)
        .then(response => response.json())
        .then(courses => {
            console.log('Cours chargés:', courses);

            const courseSelect = document.getElementById('course');
            if (courseSelect) {
                // Vider les options existantes sauf la première
                while (courseSelect.options.length > 1) {
                    courseSelect.remove(1);
                }

                // Ajouter les nouveaux cours
                courses.forEach(course => {
                    const option = document.createElement('option');
                    option.value = course.id;
                    option.textContent = course.name;
                    courseSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des cours:', error);
            alert('Erreur lors du chargement des cours: ' + error.message);
        });
}

// Chargement des exercices pour un cours
function loadExercises(courseId) {
    if (!courseId) return;
    console.log('Chargement des exercices pour le cours ID:', courseId);

    fetch(`${API_BASE_URL}/api/exercises?course_id=${courseId}`)
        .then(response => response.json())
        .then(exercises => {
            console.log('Exercices chargés:', exercises);

            const exerciseSelect = document.getElementById('exercise');
            if (exerciseSelect) {
                // Vider toutes les options
                exerciseSelect.innerHTML = '';

                // Option par défaut
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Sélectionnez un exercice';
                exerciseSelect.appendChild(defaultOption);

                // Ajouter les nouveaux exercices
                exercises.forEach(exercise => {
                    const option = document.createElement('option');
                    option.value = exercise.id;
                    option.textContent = exercise.name;
                    exerciseSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des exercices:', error);
            alert('Erreur lors du chargement des exercices: ' + error.message);
        });
}

// Gestion de la soumission de code
function handleCodeSubmission(e) {
    e.preventDefault();
    console.log('Traitement de la soumission de code...');

    if (!currentUser) {
        alert('Veuillez vous connecter pour soumettre du code.');
        window.location.href = 'authentication.html';
        return;
    }

    const courseId = document.getElementById('course').value;
    const exerciseId = document.getElementById('exercise').value;
    const languageId = document.getElementById('language').value;
    const codeFile = document.getElementById('code-file').files[0];

    if (!courseId || !exerciseId || !languageId || !codeFile) {
        alert('Veuillez remplir tous les champs et sélectionner un fichier.');
        return;
    }

    // Lecture du fichier
    const reader = new FileReader();
    reader.onload = function(e) {
        const code = e.target.result;
        submitCode(courseId, exerciseId, languageId, code);
    };
    reader.readAsText(codeFile);
}

// Soumission du code à l'API
function submitCode(courseId, exerciseId, languageId, code) {
    console.log('Soumission du code à l\'API...');

    // Mise à jour de l'interface
    const statusElement = document.getElementById('upload-status');
    const progressElement = statusElement.querySelector('.progress');
    const messageElement = statusElement.querySelector('.status-message');

    statusElement.classList.remove('hidden');
    messageElement.textContent = 'Envoi en cours...';
    progressElement.style.width = '25%';

    // Préparation des données
    const submissionData = {
        user_id: currentUser.id,
        course_id: parseInt(courseId),
        exercise_id: parseInt(exerciseId),
        language_id: parseInt(languageId),
        code: code
    };

    console.log('Données de soumission:', submissionData);

    fetch(`${API_BASE_URL}/api/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(submissionData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Soumission réussie:', data);
        messageElement.textContent = 'Code soumis avec succès, traitement en cours...';
        progressElement.style.width = '50%';

        // Vérification périodique du statut
        checkSubmissionStatus(data.submission_id, statusElement, progressElement, messageElement);
    })
    .catch(error => {
        console.error('Erreur lors de la soumission:', error);
        messageElement.textContent = 'Erreur lors de la soumission: ' + error.message;
        statusElement.classList.add('error');
    });
}

// Vérification du statut d'une soumission
function checkSubmissionStatus(submissionId, statusElement, progressElement, messageElement) {
    console.log('Vérification du statut de la soumission:', submissionId);

    const pollInterval = setInterval(() => {
        fetch(`${API_BASE_URL}/api/status/${submissionId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Statut de la soumission:', data);

                switch(data.status) {
                    case 'queued':
                        messageElement.textContent = 'En attente de traitement...';
                        progressElement.style.width = '50%';
                        break;
                    case 'processing':
                        messageElement.textContent = 'Traitement en cours...';
                        progressElement.style.width = '75%';
                        break;
                    case 'completed':
                        clearInterval(pollInterval);
                        messageElement.textContent = `Traitement terminé. Score: ${data.score}%`;
                        progressElement.style.width = '100%';
                        statusElement.classList.add('success');

                        // Afficher les détails si disponibles
                        if (data.details && data.details.output) {
                            const outputElement = document.createElement('pre');
                            outputElement.textContent = data.details.output;
                            statusElement.appendChild(outputElement);
                        }
                        break;
                    case 'error':
                        clearInterval(pollInterval);
                        messageElement.textContent = 'Erreur lors du traitement.';
                        statusElement.classList.add('error');
                        break;
                    default:
                        messageElement.textContent = `Statut: ${data.status}`;
                }
            })
            .catch(error => {
                console.error('Erreur lors de la vérification du statut:', error);
                clearInterval(pollInterval);
                messageElement.textContent = 'Erreur lors de la vérification du statut: ' + error.message;
                statusElement.classList.add('error');
            });
    }, 2000); // Vérification toutes les 2 secondes
}

// Chargement des soumissions de l'utilisateur
function loadUserSubmissions() {
    if (!currentUser) return;
    console.log('Chargement des soumissions pour l\'utilisateur:', currentUser.id);

    fetch(`${API_BASE_URL}/api/submissions?user_id=${currentUser.id}`)
        .then(response => response.json())
        .then(submissions => {
            console.log('Soumissions chargées:', submissions);

            const tableBody = document.getElementById('submissions-table');
            if (tableBody) {
                tableBody.innerHTML = '';

                if (submissions.length === 0) {
                    const row = document.createElement('tr');
                    const cell = document.createElement('td');
                    cell.colSpan = 5;
                    cell.textContent = 'Aucune soumission trouvée';
                    cell.style.textAlign = 'center';
                    row.appendChild(cell);
                    tableBody.appendChild(row);
                    return;
                }

                submissions.forEach(sub => {
                    const row = document.createElement('tr');

                    // Cours
                    const courseCell = document.createElement('td');
                    courseCell.textContent = sub.course_name;
                    row.appendChild(courseCell);

                    // Exercice
                    const exerciseCell = document.createElement('td');
                    exerciseCell.textContent = sub.exercise_name;
                    row.appendChild(exerciseCell);

                    // Langage (à adapter selon votre structure)
                    const langCell = document.createElement('td');
                    langCell.textContent = sub.language_id === 1 ? 'Python' : 'C';
                    row.appendChild(langCell);

                    // Statut
                    const statusCell = document.createElement('td');
                    statusCell.textContent = sub.status;
                    row.appendChild(statusCell);

                    // Score
                    const scoreCell = document.createElement('td');
                    scoreCell.textContent = sub.score !== null ? `${sub.score}%` : 'N/A';
                    row.appendChild(scoreCell);

                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des soumissions:', error);

            if (document.getElementById('submissions-table')) {
                const row = document.createElement('tr');
                const cell = document.createElement('td');
                cell.colSpan = 5;
                cell.textContent = 'Erreur lors du chargement des soumissions: ' + error.message;
                cell.style.textAlign = 'center';
                row.appendChild(cell);
                document.getElementById('submissions-table').appendChild(row);
            }
        });
}
