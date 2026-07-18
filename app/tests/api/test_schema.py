import json

from django.urls import reverse


def test_schema_and_docs_are_public_and_schema_marks_security(api_client):
    schema_response = api_client.get(
        reverse("api-schema"),
        HTTP_ACCEPT="application/vnd.oai.openapi+json",
        HTTP_AUTHORIZATION="Bearer malformed",
    )
    docs_response = api_client.get(
        reverse("api-docs"), HTTP_AUTHORIZATION="Bearer malformed"
    )

    assert schema_response.status_code == 200
    assert docs_response.status_code == 200

    schema = json.loads(schema_response.content)
    assert "/health/" not in schema["paths"]

    public_paths = (
        "/api/v1/auth/token/",
        "/api/v1/auth/token/refresh/",
        "/api/v1/auth/token/verify/",
        "/api/schema/",
        "/api/docs/",
    )
    for path in public_paths:
        assert path in schema["paths"]
        for operation in schema["paths"][path].values():
            assert "security" not in operation

    protected_paths = {
        "/api/v1/users/me/": ("get",),
        "/api/v1/projects/": ("get", "post"),
        "/api/v1/projects/{id}/": ("get", "patch", "delete"),
        "/api/v1/memberships/": ("get", "post"),
        "/api/v1/memberships/{id}/": ("get", "patch", "delete"),
        "/api/v1/tasks/": ("get", "post"),
        "/api/v1/tasks/{id}/": ("get", "patch", "delete"),
    }
    for path, methods in protected_paths.items():
        assert path in schema["paths"]
        for method in methods:
            assert schema["paths"][path][method]["security"] == [{"jwtAuth": []}]

    project_request = schema["components"]["schemas"]["ProjectRequest"]
    task_create_request = schema["components"]["schemas"]["TaskCreateRequest"]
    task_update_request = schema["components"]["schemas"]["PatchedTaskUpdateRequest"]
    membership_update_request = schema["components"]["schemas"][
        "PatchedProjectMembershipUpdateRequest"
    ]
    assert "owner" not in project_request["properties"]
    assert "creator" not in task_create_request["properties"]
    assert "creator" not in task_update_request["properties"]
    assert "project" not in task_update_request["properties"]
    assert "project" not in membership_update_request["properties"]
    assert "user" not in membership_update_request["properties"]
    assert "jwtAuth" in schema["components"]["securitySchemes"]
