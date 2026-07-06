#!/bin/sh

set -eu

schema=${1:-http://127.0.0.1:8000/v1/openapi.json}

if ! command -v schemathesis >/dev/null 2>&1; then
  echo "Install requirements-dev.txt to run Schemathesis 4.22.1." >&2
  exit 2
fi

schemathesis run "$schema" \
  --include-operation-id api_v1_root_v1_get \
  --include-operation-id api_v1_list_opportunities_v1_opportunities_get \
  --include-operation-id api_v1_list_organizers_v1_organizers_get \
  --include-operation-id api_v1_list_venues_v1_venues_get \
  --include-operation-id api_v1_list_operations_v1_operations_get \
  --include-operation-id api_v1_planning_v1_planning_get \
  --include-operation-id api_v1_description_v1_api_description_get \
  --include-operation-id api_v1_openapi_json_v1_openapi_json_get \
  --include-operation-id api_v1_openapi_yaml_v1_openapi_yaml_get \
  --include-operation-id api_v1_schema_catalog_v1_schemas_get \
  --phases coverage,fuzzing \
  --checks not_a_server_error,status_code_conformance,content_type_conformance,response_schema_conformance,positive_data_acceptance \
  --max-examples 25
