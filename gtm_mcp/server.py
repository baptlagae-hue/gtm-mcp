"""
Google Tag Manager (GTM) Local MCP Server.
Integrates GTM API v2 with FastMCP, utilizing local Application Default Credentials (ADC).
Enforces governance guardrails on write operations.
"""

import os
import sys
import google.auth
import google.auth.transport.requests
from google.auth.transport.requests import AuthorizedSession
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Google Tag Manager")

# Governance Naming Convention Prefix (override with GTM_WORKSPACE_PREFIX env var)
WORKSPACE_PREFIX = os.environ.get("GTM_WORKSPACE_PREFIX", "IA | ")
GTM_API_BASE = "https://tagmanager.googleapis.com/tagmanager/v2"

def get_session():
    """
    Obtains authenticated Google API session using local Application Default Credentials (ADC).
    """
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/tagmanager.edit.containers']
    )
    req = google.auth.transport.requests.Request()
    credentials.refresh(req)
    return AuthorizedSession(credentials)

def verify_workspace_prefix(session, workspace_path: str) -> bool:
    """
    Checks if a workspace starts with the allowed naming convention prefix.
    Returns True if valid, False otherwise.
    """
    url = f"{GTM_API_BASE}/{workspace_path}"
    response = session.get(url)
    if response.status_code != 200:
        raise ValueError(f"Could not retrieve workspace information: {response.text}")
    
    workspace_data = response.json()
    name = workspace_data.get("name", "")
    return name.startswith(WORKSPACE_PREFIX), name


# --- Read Operations (Low-Risk) ---

@mcp.tool()
def list_gtm_accounts():
    """
    List all Google Tag Manager accounts accessible with your active credentials.
    """
    session = get_session()
    url = f"{GTM_API_BASE}/accounts"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list accounts: {response.text}"}
    return response.json()

@mcp.tool()
def list_gtm_containers(parent: str):
    """
    List GTM containers for a given account.
    
    Args:
        parent: The parent account path (e.g., 'accounts/123456')
    """
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/containers"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list containers: {response.text}"}
    return response.json()

@mcp.tool()
def list_gtm_workspaces(parent: str):
    """
    List workspaces inside a GTM container.
    
    Args:
        parent: The parent container path (e.g., 'accounts/123456/containers/78901')
    """
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/workspaces"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list workspaces: {response.text}"}
    return response.json()

@mcp.tool()
def list_gtm_tags(parent: str):
    """
    List tags inside a GTM workspace.
    
    Args:
        parent: The workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
    """
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/tags"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list tags: {response.text}"}
    return response.json()

@mcp.tool()
def list_gtm_triggers(parent: str):
    """
    List triggers inside a GTM workspace.
    
    Args:
        parent: The workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
    """
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/triggers"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list triggers: {response.text}"}
    return response.json()

@mcp.tool()
def list_gtm_variables(parent: str):
    """
    List variables inside a GTM workspace.
    
    Args:
        parent: The workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
    """
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/variables"
    response = session.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to list variables: {response.text}"}
    return response.json()


# --- Write Operations (High-Risk, Protected by Governance Rules) ---

@mcp.tool()
def create_gtm_workspace(parent: str, name: str, description: str = None):
    """
    Create a new workspace in a GTM container. Enforces strict naming conventions.
    
    Args:
        parent: The parent container path (e.g., 'accounts/123456/containers/78901')
        name: The name of the workspace. MUST start with the governance prefix (default 'IA | ', override with GTM_WORKSPACE_PREFIX)
        description: Optional description of the workspace.
    """
    if not name.startswith(WORKSPACE_PREFIX):
        return {
            "error": (
                f"Governance Policy Violation: Workspace name '{name}' must start "
                f"with the prefix '{WORKSPACE_PREFIX}' for compliance."
            )
        }
    
    session = get_session()
    url = f"{GTM_API_BASE}/{parent}/workspaces"
    payload = {"name": name}
    if description:
        payload["description"] = description
        
    response = session.post(url, json=payload)
    if response.status_code != 200:
        return {"error": f"Failed to create workspace: {response.text}"}
    return response.json()

@mcp.tool()
def create_gtm_tag(parent: str, tag_data: dict):
    """
    Create a new tag in a GTM workspace. Enforced to only run in workspaces matching the governance prefix (default 'IA | ').
    
    Args:
        parent: The parent workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
        tag_data: The JSON payload for the tag (matching GTM API v2 schema)
    """
    session = get_session()
    try:
        is_allowed, ws_name = verify_workspace_prefix(session, parent)
        if not is_allowed:
            return {
                "error": (
                    f"Governance Policy Violation: Modifications are only allowed inside "
                    f"workspaces starting with '{WORKSPACE_PREFIX}'. The workspace '{ws_name}' "
                    f"({parent}) is protected and cannot be edited."
                )
            }
    except Exception as e:
        return {"error": str(e)}
        
    url = f"{GTM_API_BASE}/{parent}/tags"
    response = session.post(url, json=tag_data)
    if response.status_code != 200:
        return {"error": f"Failed to create tag: {response.text}"}
    return response.json()

@mcp.tool()
def create_gtm_trigger(parent: str, trigger_data: dict):
    """
    Create a new trigger in a GTM workspace. Enforced to only run in workspaces matching the governance prefix (default 'IA | ').
    
    Args:
        parent: The parent workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
        trigger_data: The JSON payload for the trigger (matching GTM API v2 schema)
    """
    session = get_session()
    try:
        is_allowed, ws_name = verify_workspace_prefix(session, parent)
        if not is_allowed:
            return {
                "error": (
                    f"Governance Policy Violation: Modifications are only allowed inside "
                    f"workspaces starting with '{WORKSPACE_PREFIX}'. The workspace '{ws_name}' "
                    f"({parent}) is protected and cannot be edited."
                )
            }
    except Exception as e:
        return {"error": str(e)}
        
    url = f"{GTM_API_BASE}/{parent}/triggers"
    response = session.post(url, json=trigger_data)
    if response.status_code != 200:
        return {"error": f"Failed to create trigger: {response.text}"}
    return response.json()

@mcp.tool()
def create_gtm_variable(parent: str, variable_data: dict):
    """
    Create a new variable in a GTM workspace. Enforced to only run in workspaces matching the governance prefix (default 'IA | ').
    
    Args:
        parent: The parent workspace path (e.g., 'accounts/123456/containers/78901/workspaces/12')
        variable_data: The JSON payload for the variable (matching GTM API v2 schema)
    """
    session = get_session()
    try:
        is_allowed, ws_name = verify_workspace_prefix(session, parent)
        if not is_allowed:
            return {
                "error": (
                    f"Governance Policy Violation: Modifications are only allowed inside "
                    f"workspaces starting with '{WORKSPACE_PREFIX}'. The workspace '{ws_name}' "
                    f"({parent}) is protected and cannot be edited."
                )
            }
    except Exception as e:
        return {"error": str(e)}
        
    url = f"{GTM_API_BASE}/{parent}/variables"
    response = session.post(url, json=variable_data)
    if response.status_code != 200:
        return {"error": f"Failed to create variable: {response.text}"}
    return response.json()

def main():
    # Run server via stdio transport
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
