#!/bin/bash
set -e

if [[ -f ".env" ]]; then
    set -a && source .env && set +a
    echo ".env file loaded successfully."
else
    echo ".env file not found, creating .env from .env.example."
    cp .env.example .env
fi

# List of all possible options if no option is passed or --help is passed
if [ $# -eq 0 ] || [ $1 == "--help" ]; then
printf "Usage: $0 [options]
Options:
    -i|--install: Install the app
        -nc|--no-cache: Build images without cache
        -rv|--remove-volumes: Remove volumes while installing
    -b|--backup: Backup the DB, default is user data
        --user: Backup only user data
        --full: Backup full DB
        -p|--backup-path: Path to store the backups. Default backup path is /home/projects/db_backups/<PROJECT_NAME>
    -r|--restore: Restores the latest backup of the DB if no file is specified. If a file is specified, restores that file.
        --user: Restore only user data
        --full: Restore full DB
        -f|--file: Exact path of the file to restore
    -u|--uninstall: Uninstall the app
        -rv|--remove-volumes: Remove volumes while uninstalling
    --dev: Do a development deployment
    --help: Show this help message \n"
    exit 0
fi

PROJECT_NAME=$STACK_NAME
DB_VOLUME_NAME=$PROJECT_NAME\_app-db-data
DB_CONTAINER_NAME=$PROJECT_NAME-db
LOGS_DIR="/tmp/project_logs"
CLEAN_BUILD=false
CLEAR_VOLUMES=false
RUN_INSTALL=false
RUN_UNINSTALL=false
BACKUP=false
RESTORE=false
USER=true
FULL=false
BACKUP_TABLES=("email_status" "email_status_id_seq" "group" "group_id_seq" "invitation" "invitation_id_seq" "invitation_registrations" "notification" "notification_id_seq" "password_reset" "password_reset_id_seq" "user" "user_groups" "user_settings" "user_settings_id_seq")
BACKUP_DIR=/home/projects/db_backups/$PROJECT_NAME
DB_USER=$POSTGRES_USER
DB_NAME=$POSTGRES_DB
MAX_BACKUPS=10
RESTORE_FILE=""
COMPOSE_FILE="compose.yml"
COMPOSE_OVERRIDE_FILE="compose.prod.yml"
DEV_DEPLOYMENT=false

while [[ $# > 0 ]]; do
    case $1 in
        -rv|--remove-volumes)
            CLEAR_VOLUMES=true
            ;;
        -i|--install)
            RUN_INSTALL=true
            ;;
        -nc|--no-cache)
            CLEAN_BUILD=true
            ;;
        -b|--backup)
            BACKUP=true
            ;;
        -r|--restore)
            RESTORE=true
            ;;
        -f|--file)
            RESTORE_FILE=$2
            shift
            ;;
        -p| --backup-path)
            BACKUP_DIR=$2
            shift
            ;;
        --user)
            USER=true
            ;;
        --full)
            FULL=true
            USER=false
            ;;
        -u|--uninstall)
            RUN_UNINSTALL=true
            ;;
        --dev)
            DEV_DEPLOYMENT=true
            COMPOSE_OVERRIDE_FILE="compose.override.yml"
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
    shift
done

remove_app() {
    echo "Bringing down existing deployment"
    if $CLEAR_VOLUMES; then
        echo "Removing containers and volumes"
        docker compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE_FILE down -v
    else
        echo "Removing containers without removing volumes"
        docker compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE_FILE down
    fi
}

install_app() {
    # Bring the app down if it is currently up
    if docker ps -a | grep -q $PROJECT_NAME; then
        remove_app
    fi

    echo "Installing the app"
    if $CLEAN_BUILD; then
        echo "Building images without cache"
        docker compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE_FILE build --no-cache
    else
        docker compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE_FILE build
    fi
    docker compose -f $COMPOSE_FILE -f $COMPOSE_OVERRIDE_FILE up -d --remove-orphans
    echo "App deployed successfully"
}

uninstall_app() {
    if ! docker ps -a | grep -q $PROJECT_NAME; then
        echo "No container with name $PROJECT_NAME found. App is not currently deployed."
        return
    else
        remove_app
    fi
    echo "App uninstalled successfully"
}

is_db_running() {
    if docker ps -a | grep -q $DB_CONTAINER_NAME; then
        return 0
    else
        return 1
    fi
}

getFilename() {
    if $FULL; then
        filename="fulldump"
    else
        filename="userdatadump"
    fi
}

backup() {
    if ! is_db_running; then
        echo "DB is not running, cannot backup."
        return
    fi

    getFilename

    if $FULL; then
        echo "Taking full backup of DB"
        docker exec $DB_CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $filename
    else
        echo "Taking backup of user data"
        #create backup tables string
        all_tables=""
        for table in ${BACKUP_TABLES[@]}; do
            all_tables="${all_tables} -t $table"
        done
        #take back up of required tables mentioned in $all_tables
        docker exec $DB_CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME --disable-triggers --data-only --inserts $all_tables > $filename
    fi

    if ! [ -d "$BACKUP_DIR" ]; then
        echo "Backup directory doesn't exist, creating it..."
        mkdir -p "$BACKUP_DIR"
        if [ $? -ne 0 ]; then
            echo "Error: Failed to create backup directory."
            exit 1
        fi
    fi

    #backup the dumpfile  in backup directory
    timestamp=$(date "+%Y%m%d-%H%M%S")
    backup_file="$BACKUP_DIR/$filename-$timestamp"
    echo "Copying backup file to backup directory..."
    if cp "$filename" "$backup_file"; then
        echo "Backup file created at: $backup_file"
        rm "$filename"
    else
        echo "Error: Failed to copy backup file."
        exit 1
    fi

    #keep only last 10 backups and delete the rest
    echo "Pruning old backups, keeping the last $MAX_BACKUPS..."
    ls -Art $BACKUP_DIR/$filename-* | head -n -$MAX_BACKUPS | xargs rm -f

    if [ $? -eq 0 ]; then
    echo "Backup process successful" 
    else
        echo "Backup process failed."
        exit 1
    fi
}

# Restore the DB from the latest backup file
restore() {
    if ! is_db_running; then
        echo "DB is not running, cannot restore."
        return
    fi

    if [[ -n $RESTORE_FILE ]]; then
        echo "Restoring from file:" $RESTORE_FILE

        #copy the backed up file to DB container
        docker cp $RESTORE_FILE $DB_CONTAINER_NAME:/
        # get the filename from the path
        RESTORE_FILE=$(basename $RESTORE_FILE)
    else
        echo "Looking for previous backups"
        getFilename
        RESTORE_FILE=$(ls -Artp $BACKUP_DIR/$filename-* | tail -1| xargs -n 1 basename)

        if [[ -z $RESTORE_FILE ]]; then
            echo "No full backup found to restore"
            return
        fi

        echo "Found a previous backup to restore:" $RESTORE_FILE

        #copy the backed up file to DB container
        docker cp $BACKUP_DIR/$RESTORE_FILE $DB_CONTAINER_NAME:/
    fi

    echo "Starting restore process"

    if $USER; then
        docker exec $DB_CONTAINER_NAME psql -q -U $DB_USER $DB_NAME -c 'TRUNCATE TABLE "user" CASCADE;'
    else
        # drop all tables
        docker exec $DB_CONTAINER_NAME psql -q -U $DB_USER $DB_NAME -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
    fi

    docker exec $DB_CONTAINER_NAME psql -q -U $DB_USER $DB_NAME -f $RESTORE_FILE
    docker exec $DB_CONTAINER_NAME rm $RESTORE_FILE

    echo "Restore complete"
}

if $BACKUP; then
    backup
fi
if $RUN_INSTALL; then
    if ! $DEV_DEPLOYMENT; then
        backup
    fi
    install_app
fi
if $RESTORE; then
    restore
fi
if $RUN_UNINSTALL; then
    uninstall_app
fi
