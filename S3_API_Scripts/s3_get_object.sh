#!/bin/bash

aws s3api get-object --bucket $1 --key $2  $3