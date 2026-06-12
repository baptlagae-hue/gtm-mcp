import google.auth
import google.auth.transport.requests
from google.auth.transport.requests import AuthorizedSession
import json

WORKSPACE_PREFIX = "MS | "
GTM_API_BASE = "https://tagmanager.googleapis.com/tagmanager/v2"

# Test Target Container
container_path = "accounts/6213496647/containers/175438363"

def get_session():
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/tagmanager.edit.containers']
    )
    req = google.auth.transport.requests.Request()
    credentials.refresh(req)
    return AuthorizedSession(credentials)

def verify_workspace_prefix(session, workspace_path: str) -> bool:
    url = f"{GTM_API_BASE}/{workspace_path}"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(f"Could not retrieve workspace: {response.text}")
    workspace_data = response.json()
    name = workspace_data.get("name", "")
    return name.startswith(WORKSPACE_PREFIX), name

# --- Simulated Tool Endpoints with Guardrails ---

def local_create_workspace(session, parent_container: str, name: str, description: str = None):
    # Rule 1: Validate name prefix
    if not name.startswith(WORKSPACE_PREFIX):
        return {
            "error": (
                f"Governance Policy Violation: Workspace name '{name}' must start "
                f"with the prefix '{WORKSPACE_PREFIX}' for compliance."
            )
        }
    
    url = f"{GTM_API_BASE}/{parent_container}/workspaces"
    payload = {"name": name}
    if description:
        payload["description"] = description
        
    response = session.post(url, json=payload)
    if response.status_code != 200:
        return {"error": f"Failed to create workspace: {response.text}"}
    return response.json()

def local_create_variable(session, parent_workspace: str, variable_data: dict):
    # Rule 2: Verify target workspace prefix
    try:
        is_allowed, ws_name = verify_workspace_prefix(session, parent_workspace)
        if not is_allowed:
            return {
                "error": (
                    f"Governance Policy Violation: Modifications are only allowed inside "
                    f"workspaces starting with '{WORKSPACE_PREFIX}'. The workspace '{ws_name}' "
                    f"({parent_workspace}) is protected."
                )
            }
    except Exception as e:
        return {"error": str(e)}
        
    url = f"{GTM_API_BASE}/{parent_workspace}/variables"
    response = session.post(url, json=variable_data)
    if response.status_code != 200:
        return {"error": f"Failed to create variable: {response.text}"}
    return response.json()


def main():
    print("Obtaining session...")
    session = get_session()
    
    print("\n--- TEST 1: Attempt to create workspace with non-compliant name ---")
    bad_name = "Antigravity Test Workspace"
    res1 = local_create_workspace(session, container_path, bad_name)
    print("Result:")
    print(json.dumps(res1, indent=2))
    assert "error" in res1 and "Governance Policy Violation" in res1["error"]
    print("SUCCESS: Non-compliant workspace creation was blocked by the guardrail!")

    print("\n--- TEST 2: Attempt to create workspace with compliant name ---")
    good_name = "MS | Test Workspace"
    res2 = local_create_workspace(session, container_path, good_name)
    print("Result:")
    print(json.dumps(res2, indent=2))
    
    workspace_path = None
    if "error" in res2:
        if "duplicate name" in res2["error"]:
            print("Workspace already exists, fetching path...")
            list_res = session.get(f"{GTM_API_BASE}/{container_path}/workspaces")
            if list_res.status_code == 200:
                workspaces = list_res.json().get("workspace", [])
                for ws in workspaces:
                    if ws.get("name") == good_name:
                        workspace_path = ws.get("path")
                        break
        if not workspace_path:
            print(f"FAILED to create compliant workspace: {res2['error']}")
            return
    else:
        workspace_path = res2.get("path")
        
    print(f"SUCCESS: Compliant workspace found/created at path: {workspace_path}")

    # Find the Default Workspace to test safety on existing workspaces
    print("\n--- TEST 3: Retrieve default workspace path for protection test ---")
    ws_list_response = session.get(f"{GTM_API_BASE}/{container_path}/workspaces")
    if ws_list_response.status_code == 200:
        workspaces = ws_list_response.json().get("workspace", [])
        default_ws_path = None
        for ws in workspaces:
            if ws.get("name") == "Default Workspace":
                default_ws_path = ws.get("path")
                break
        
        if default_ws_path:
            print(f"Found Default Workspace at path: {default_ws_path}")
            print("\n--- TEST 4: Attempt to create variable in Default Workspace (should be blocked) ---")
            test_var = {
                "name": "test_var_blocked",
                "type": "c", # Constant variable
                "parameter": [{"type": "template", "key": "value", "value": "test"}]
            }
            res4 = local_create_variable(session, default_ws_path, test_var)
            print("Result:")
            print(json.dumps(res4, indent=2))
            assert "error" in res4 and "Governance Policy Violation" in res4["error"]
            print("SUCCESS: Writing to protected workspace was blocked by the guardrail!")
        else:
            print("Default Workspace not found. Skipping Test 4.")
    else:
        print("Failed to list workspaces for Test 3.")

    # Test writing to the compliant workspace
    print(f"\n--- TEST 5: Attempt to create variable in our compliant workspace '{good_name}' ---")
    test_var_ok = {
        "name": "ms_test_variable",
        "type": "c",
        "parameter": [{"type": "template", "key": "value", "value": "verified_value"}]
    }
    res5 = local_create_variable(session, workspace_path, test_var_ok)
    print("Result:")
    print(json.dumps(res5, indent=2))
    if "error" in res5:
        print("FAILED to write to compliant workspace.")
    else:
        print("SUCCESS: Variable created successfully inside compliant workspace!")

if __name__ == "__main__":
    main()
