#!/bin/bash

INSIGHT_SERVICES_DATA_DIR=/etc/palette-insight-website

STATUS_FILE=${INSIGHT_SERVICES_DATA_DIR}/insight-status

LOADTABLES_LOCKFILE=/tmp/PI_ImportTables_prod.flock
REPORTING_LOCKFILE=/tmp/PI_Reporting_prod.flock

CRON_USER=insight
TEMP_CRON_FILE=${INSIGHT_SERVICES_DATA_DIR}/${CRON_USER}.cron.tmp



# ==================== STATUS ====================

header() {
  echo -e "\n\n=====[ $@ ]====="
}

# Returns the status of the services from the status file
# or the default status (STARTED) if the status file
# has not yet been created
insight_status() {
  if [[ ! -f ${TEMP_CRON_FILE} ]]; then
    header "Temporary backup crontab ${TEMP_CRON_FILE} exists"
  fi

  header "Server status"
  uptime=`cat /proc/uptime | cut -f1 -d.`
  upDays=$((uptime/60/60/24))
  upHours=$((uptime/60/60%24))
  upMins=$((uptime/60%60))
  upSecs=$((uptime%60))
  echo "uptime: $upDays day, $upHours:$upMins:$upSecs"

  header "Greenplum status"
  service greenplum status

  header "Version Info"
  sudo rpm -qa | grep palette

  header "Palette Insight Services status"
  supervisorctl status

  header "Current crontab used for $CRON_USER"
  crontab -l -u $CRON_USER


  header "Currently running talend jobs"
  pgrep -fl "flock /opt/palette-insight-talend" | egrep -o 'PI_[^\.]*' | xargs -n 1 echo " + "

}



# ==================== STOP ====================

insight_stop() {

  header "Stopping Palette Insight Services"

  insight_backup_crontab

  # Kill the reporting job if its running
  echo "+ Killing Palette Insight Reporting"
  # As pkill return 0 only if one or more processes matched the criteria,
  # we have to do this ugly workaround
  pkill -f "flock -n ${REPORTING_LOCKFILE}" || true

  echo "--> Waiting for loadtables to finish"
  # Wait with flock for the loadtables to finish
  flock ${LOADTABLES_LOCKFILE} echo "<-- Loadtables finished"

  # Stop GPFDIST
  echo "+ Stopping GPFDIST"
  supervisorctl stop insight-gpfdist

  # Now we can stop greenplum
  service greenplum stop
}

# ==================== START ====================

insight_start() {

  header "Starting Palette Insight Services"

  # Start up greenplum
  service greenplum start

  # Stop GPFDIST
  echo "+ Starting GPFDIST"
  supervisorctl start insight-gpfdist

  # Check if we actually have a crontab saved
  if [[ ! -f ${TEMP_CRON_FILE} ]]; then
    echo "No crontab has been saved using stop() to ${TEMP_CRON_FILE}. Please use this script to manually stop all services..."
    exit 4
  else
     insight_restore_crontab
  fi
}


# ==================== RESTORE CRONTAB ====================

insight_clean_crontab_backup() {
    echo "+ Removing temporary crontab ${TEMP_CRON_FILE}"
    rm ${TEMP_CRON_FILE}
}


insight_restore_crontab() {
    # Re-enable the crontab
    echo "+ Re-enabling crontab from ${TEMP_CRON_FILE}"

    # Re-add the backup crontab
    crontab -u $CRON_USER $TEMP_CRON_FILE

    # Remove the backup crontab
    insight_clean_crontab_backup
}

insight_backup_crontab() {
    # Disable crontab temporarily

    if [[ -f ${TEMP_CRON_FILE} ]]; then
        echo "The crontab backup in ${TEMP_CRON_FILE} is already present. Please delete it to signal that you know what you are doing."
        exit 4
    fi

    echo "+ Disabling crontab for user $CRON_USER"
    crontab -l -u $CRON_USER >$TEMP_CRON_FILE
    crontab -r -u $CRON_USER
}


# ==================== SELECT COMMAND ====================

COMMAND=$1

case $COMMAND in
    start)
        insight_start
        ;;

    stop)
        insight_stop
        ;;

    status)
        insight_status
        ;;

    restore_crontab)
        insight_restore_crontab
        ;;

    backup_crontab)
        insight_backup_crontab
        ;;

    clean_crontab)
        insight_clean_crontab_backup
        ;;


    *)
        # Print help
        echo "Usage: $0 {start|stop|restore_crontab|backup_crontab|clean_crontab}" 1>&2
        exit 1
        ;;
esac

header "OK"
exit 0

