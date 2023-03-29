#!/bin/bash

echo "Granting read permission to a user for an s3 object"

aws s3api put-object-acl --bucket $1 --key $2 --grant-read id=$3