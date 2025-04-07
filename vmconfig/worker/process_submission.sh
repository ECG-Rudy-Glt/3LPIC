#!/bin/bash

SUBMISSION_FILE=$1
WORK_DIR="/tmp/coursero_$(date +%s%N)"
mkdir -p $WORK_DIR
chmod 700 $WORK_DIR

# Configuration de la base de données
DB_HOST="192.168.159.229"  # IP de votre Master DB
DB_PORT="5432"
DB_NAME="coursero"
DB_USER="coursero"
DB_PASSWORD="coursero_secure_password"

# Logs pour le débogage
echo "$(date): Processing submission file: $SUBMISSION_FILE" >> /var/log/coursero_processing.log

# Extraction des données
SUBMISSION_ID=$(jq -r '.submission_id' $SUBMISSION_FILE)
USER_ID=$(jq -r '.user_id' $SUBMISSION_FILE)
COURSE_ID=$(jq -r '.course_id' $SUBMISSION_FILE)
EXERCISE_ID=$(jq -r '.exercise_id' $SUBMISSION_FILE)
LANGUAGE_ID=$(jq -r '.language_id' $SUBMISSION_FILE)
CODE=$(jq -r '.code' $SUBMISSION_FILE)

echo "$(date): Submission details: ID=$SUBMISSION_ID, User=$USER_ID, Course=$COURSE_ID, Exercise=$EXERCISE_ID, Language=$LANGUAGE_ID" >> /var/log/coursero_processing.log

# Récupération des arguments de test et de la sortie attendue
TEST_ARGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT arguments FROM exercise_tests WHERE exercise_id = $EXERCISE_ID" | tr -d ' ')
EXPECTED_OUTPUT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT expected_output FROM exercise_tests WHERE exercise_id = $EXERCISE_ID" | tr -d ' ')

echo "$(date): Test arguments: '$TEST_ARGS', Expected output: '$EXPECTED_OUTPUT'" >> /var/log/coursero_processing.log

# Récupération du code de langage
LANGUAGE_CODE=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT language_code FROM languages WHERE language_id = $LANGUAGE_ID" | tr -d ' ')

echo "$(date): Language ID: $LANGUAGE_ID, Language Code: $LANGUAGE_CODE" >> /var/log/coursero_processing.log

# Préparation et exécution du code selon le langage
if [ "$LANGUAGE_CODE" == "python" ]; then
    echo "$(date): Processing Python code" >> /var/log/coursero_processing.log
    echo "$CODE" > $WORK_DIR/submission.py
    chmod +x $WORK_DIR/submission.py
    cd $WORK_DIR

    # Exécution sécurisée sans cgroups
    RESULT=$(timeout 10s python3 submission.py $TEST_ARGS 2>&1)
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 124 ]; then
        RESULT="Timeout: Script execution took too long (>10s)"
    fi

elif [ "$LANGUAGE_CODE" == "c" ]; then
    echo "$(date): Processing C code" >> /var/log/coursero_processing.log
    echo "$CODE" > $WORK_DIR/submission.c
    cd $WORK_DIR

    # Compilation
    gcc -o submission submission.c 2> compile_errors.txt
    if [ $? -ne 0 ]; then
        RESULT="Compilation error: $(cat compile_errors.txt)"
    else
        # Exécution sécurisée sans cgroups
        RESULT=$(timeout 10s ./submission $TEST_ARGS 2>&1)
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 124 ]; then
            RESULT="Timeout: Program execution took too long (>10s)"
        fi
    fi

else
    RESULT="Unsupported language: $LANGUAGE_CODE"
fi

echo "$(date): Execution result: '$RESULT'" >> /var/log/coursero_processing.log

# Calcul du score
if [ "$RESULT" == "$EXPECTED_OUTPUT" ]; then
    SCORE=100
    echo "$(date): Perfect match! Score: 100%" >> /var/log/coursero_processing.log
else
    # Calcul basé sur une comparaison simple
    # Vous pouvez améliorer cette logique selon vos besoins
    EXPECTED_LEN=${#EXPECTED_OUTPUT}
    RESULT_LEN=${#RESULT}

    if [ $EXPECTED_LEN -eq 0 ]; then
        SCORE=0
    else
        # Compter combien de caractères de l'output attendu sont trouvés dans le résultat
        FOUND=$(echo "$RESULT" | grep -o "$EXPECTED_OUTPUT" | wc -c)
        SCORE=$((FOUND * 100 / EXPECTED_LEN))

        # Limiter à 0-100
        if [ $SCORE -gt 100 ]; then
            SCORE=100
        elif [ $SCORE -lt 0 ]; then
            SCORE=0
        fi
    fi

    echo "$(date): Partial match. Score: $SCORE%" >> /var/log/coursero_processing.log
fi

# Échappement JSON pour le résultat
RESULT_JSON=$(echo "$RESULT" | sed 's/"/\\"/g')

# Sauvegarde en DB
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
INSERT INTO submissions (submission_id, user_id, exercise_id, language_id, status, score, details, submit_time, completion_time)
VALUES ('$SUBMISSION_ID', '$USER_ID', $EXERCISE_ID, $LANGUAGE_ID, 'completed', $SCORE, '{\"output\": \"$RESULT_JSON\"}', NOW(), NOW())
ON CONFLICT (submission_id)
DO UPDATE SET
    status = 'completed',
    score = $SCORE,
    details = '{\"output\": \"$RESULT_JSON\"}',
    completion_time = NOW()
"

echo "$(date): Submission $SUBMISSION_ID processed with score $SCORE%" >> /var/log/coursero_processing.log

# Nettoyage
rm -rf $WORK_DIR

exit 0
