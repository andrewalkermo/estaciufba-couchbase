#!/bin/bash

# Monitor mode (used to attach into couchbase entrypoint)
set -m
# Send it to background
/entrypoint.sh couchbase-server &

check_db() {
  curl --silent http://127.0.0.1:8091/pools > /dev/null
  echo $?
}

# Variable used in echo
i=1
# Echo with
numbered_echo() {
  echo "[$i] $@"
  i=`expr $i + 1`
}

# Wait until it's ready
until [[ $(check_db) = 0 ]]; do
  >&2 numbered_echo "Waiting for Couchbase Server to be available"
  sleep 1
done

# Initialize the cluster
couchbase-cli cluster-init \
  --cluster=$HOST \
  --cluster-username=$USERNAME \
  --cluster-password=$PASSWORD \
  --cluster-ramsize=512 \
  --services=data,index,query,fts,eventing,analytics,backup

if [ $WORKER ]; then
  sleep 3
  # Add node to cluster
  couchbase-cli server-add \
      --cluster=$CLUSTER_HOST \
      --username=$USERNAME \
      --password=$PASSWORD \
      --server-add=$HOST \
      --server-add-username=$USERNAME \
      --server-add-password=$PASSWORD \
      --services=data,index,query,fts,eventing,analytics,backup

  # Rebalance
  couchbase-cli rebalance \
      --cluster=$CLUSTER_HOST \
      --username=$USERNAME \
      --password=$PASSWORD
else
  # Create a bucket
  couchbase-cli bucket-create \
      --cluster=$HOST \
      --username=$USERNAME \
      --password=$PASSWORD \
      --bucket=estaciufba \
      --bucket-type=couchbase \
      --bucket-ramsize=512

  # Create a scope and collections
  curl -X POST -s -v -u $USERNAME:$PASSWORD http://$HOST:8091/pools/default/buckets/estaciufba/scopes -d name=develop
  curl -X POST -s -v -u $USERNAME:$PASSWORD http://$HOST:8091/pools/default/buckets/estaciufba/scopes/develop/collections -d name=estacionamentos
  curl -X POST -s -v -u $USERNAME:$PASSWORD http://$HOST:8091/pools/default/buckets/estaciufba/scopes/develop/collections -d name=vagas
  curl -X POST -s -v -u $USERNAME:$PASSWORD http://$HOST:8091/pools/default/buckets/estaciufba/scopes/develop/collections -d name=vagas_acessos

  # Create a backup repository
  cbbackupmgr config --archive /backups --repo estaciufba_${HOSTNAME}

  sleep 3
  # Create a remote cluster reference
  couchbase-cli xdcr-setup \
      --cluster=$HOST \
      --username=$USERNAME \
      --password=$PASSWORD \
      --create \
      --xdcr-cluster-name=$XDCR_NAME \
      --xdcr-hostname=$XDCR_HOST \
      --xdcr-username=$XDCR_USERNAME \
      --xdcr-password=$XDCR_PASSWORD

  # Create a outgoing replication
    couchbase-cli xdcr-replicate \
      --cluster=$HOST \
      --username=$USERNAME \
      --password=$PASSWORD \
      --create \
      --xdcr-cluster-name=$XDCR_NAME \
      --xdcr-from-bucket=estaciufba \
      --xdcr-to-bucket=estaciufba

fi

numbered_echo "Attaching to couchbase-server entrypoint"

fg 1