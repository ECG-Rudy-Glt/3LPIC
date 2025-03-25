-- Création des tables
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    course_code VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE exercises (
    exercise_id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(course_id),
    exercise_name VARCHAR(255) NOT NULL,
    exercise_number INTEGER NOT NULL,
    UNIQUE(course_id, exercise_number)
);

CREATE TABLE languages (
    language_id SERIAL PRIMARY KEY,
    language_name VARCHAR(50) NOT NULL,
    language_code VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE submissions (
    submission_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    exercise_id INTEGER REFERENCES exercises(exercise_id),
    language_id INTEGER REFERENCES languages(language_id),
    score FLOAT,
    status VARCHAR(20) NOT NULL, -- 'pending', 'completed', 'error'
    details JSONB,
    submit_time TIMESTAMP DEFAULT NOW(),
    completion_time TIMESTAMP,
    UNIQUE(user_id, exercise_id, language_id, submit_time)
);

-- Table pour suivre la meilleure soumission par utilisateur/exercice/langage
CREATE TABLE best_submissions (
    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    submission_id INTEGER NOT NULL REFERENCES submissions(submission_id),
    score FLOAT NOT NULL,
    PRIMARY KEY (user_id, exercise_id, language_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id)
);

-- Trigger pour mettre à jour les meilleures soumissions
CREATE OR REPLACE FUNCTION update_best_submission()
RETURNS TRIGGER AS $$
BEGIN
    -- Si le statut n'est pas 'completed', ne rien faire
    IF NEW.status != 'completed' THEN
        RETURN NEW;
    END IF;

    -- Mettre à jour ou insérer dans best_submissions
    INSERT INTO best_submissions (user_id, exercise_id, language_id, submission_id, score)
    VALUES (NEW.user_id, NEW.exercise_id, NEW.language_id, NEW.submission_id, NEW.score)
    ON CONFLICT (user_id, exercise_id, language_id)
    DO UPDATE SET 
        submission_id = EXCLUDED.submission_id,
        score = EXCLUDED.score
    WHERE EXCLUDED.score > best_submissions.score;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER submission_completed
AFTER UPDATE OF status ON submissions
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION update_best_submission();