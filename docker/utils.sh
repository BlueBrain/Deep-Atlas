#!/bin/bash

create_users() {
  local USERS="$1"
  local GROUP="$2"
  local user_ids=()
  for x in $(echo "$USERS" | tr "," "\n")
  do
    # skip empty user entries
    if [ -z "$x" ]
    then
      continue
    fi

    # Create and configure user
    user_name="${x%/*}"
    user_id="${x#*/}"
    while [[ " ${user_ids[*]} " == *" ${user_id} "* ]]; do user_id=$(($user_id+1)); done
    user_ids+=($user_id)
    user_home="/home/${user_name}"
    useradd --create-home --uid "$user_id" --gid "$GROUP" --home-dir "$user_home" "$user_name"
    su "$user_name" -c "$(declare -f configure_user add_aliases improve_prompt configure_jupyter) &&  configure_user"
    echo "Added user ${user_name} with ID ${user_id}"
  done
}
