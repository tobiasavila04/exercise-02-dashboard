import os
import requests
import streamlit as st
import pandas as pd


API_URL = os.environ.get("API_URL", "http://api:8080")
TIMEOUT = 10


def get_health():
    try:
        resp = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "connection", "message": "Cannot connect to API"}
    except requests.exceptions.Timeout:
        return {"error": "timeout", "message": "API request timed out"}
    except Exception as e:
        return {"error": "unknown", "message": str(e)}


def get_nodes():
    try:
        resp = requests.get(f"{API_URL}/api/nodes", timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "connection"}
    except Exception:
        return {"error": "failed"}


def post_node(name: str, host: str, port: int):
    try:
        payload = {"name": name, "host": host, "port": port}
        resp = requests.post(f"{API_URL}/api/nodes", json=payload, timeout=TIMEOUT)
        return resp
    except requests.exceptions.ConnectionError:
        return None


def delete_node(name: str):
    try:
        resp = requests.delete(f"{API_URL}/api/nodes/{name}", timeout=TIMEOUT)
        return resp
    except requests.exceptions.ConnectionError:
        return None


def render_health_indicator():
    st.header("Health Indicator")
    health = get_health()
    
    if "error" in health:
        st.error(f"API Status: OFFLINE ({health.get('message', 'Connection error')})")
    else:
        status = health.get("status", "unknown")
        db_status = health.get("db", "unknown")
        nodes_count = health.get("nodes_count", 0)
        
        if status == "ok" and db_status == "connected":
            st.success("API Status: ONLINE")
            st.info(f"Database: {db_status.upper()}")
            st.metric(label="Active Nodes", value=nodes_count)
        elif status == "ok" and db_status != "connected":
            st.warning("API Status: ONLINE (Database disconnected)")
        else:
            st.error("API Status: UNHEALTHY")


def render_node_list():
    st.header("Registered Nodes")
    nodes = get_nodes()
    
    if isinstance(nodes, dict) and "error" in nodes:
        st.warning("Could not fetch nodes from API")
        return
    
    if not nodes:
        st.info("No nodes registered yet")
        return
    
    df = pd.DataFrame(nodes)
    display_cols = ["name", "host", "port", "status"]
    
    for col in display_cols:
        if col not in df.columns:
            df[col] = "N/A"
    
    display_df = df[display_cols].copy()
    display_df.columns = ["Name", "Host", "Port", "Status"]
    
    st.dataframe(display_df, use_container_width=True)


def render_registration_form():
    st.header("Register a New Node")
    
    with st.form("register_form", clear_on_submit=True):
        name = st.text_input("Node Name", placeholder="e.g., worker-01")
        host = st.text_input("Host", placeholder="e.g., 192.168.1.10")
        port = st.number_input("Port", min_value=1, max_value=65535, value=8080)
        submitted = st.form_submit_button("Register Node")
        
        if submitted:
            if not name or not host:
                st.error("Name and Host are required")
            else:
                resp = post_node(name.strip(), host.strip(), int(port))
                
                if resp is None:
                    st.error("Connection error: Could not reach API")
                elif resp.status_code == 201:
                    st.success(f"Node '{name}' registered successfully!")
                    st.rerun()
                elif resp.status_code == 409:
                    detail = resp.json().get("detail", "Unknown error")
                    st.error(f"Conflict: {detail}")
                else:
                    try:
                        detail = resp.json().get("detail", f"HTTP {resp.status_code}")
                    except Exception:
                        detail = f"HTTP {resp.status_code}"
                    st.error(f"Failed to register node: {detail}")


def render_delete_button():
    st.header("Delete a Node")
    st.caption("This performs a soft-delete (status becomes 'inactive')")
    
    with st.form("delete_form", clear_on_submit=True):
        delete_name = st.text_input("Node Name to Delete", placeholder="Enter node name")
        delete_submitted = st.form_submit_button("Delete Node", type="secondary")
        
        if delete_submitted:
            if not delete_name:
                st.error("Please enter a node name")
            else:
                resp = delete_node(delete_name.strip())
                
                if resp is None:
                    st.error("Connection error: Could not reach API")
                elif resp.status_code == 204:
                    st.success(f"Node '{delete_name}' deleted (soft-delete)")
                    st.rerun()
                elif resp.status_code == 404:
                    detail = resp.json().get("detail", "Node not found")
                    st.error(f"Not found: {detail}")
                else:
                    try:
                        detail = resp.json().get("detail", f"HTTP {resp.status_code}")
                    except Exception:
                        detail = f"HTTP {resp.status_code}"
                    st.error(f"Failed to delete node: {detail}")


def main():
    st.set_page_config(page_title="Node Registry Dashboard", layout="wide")
    st.title("Node Registry Dashboard")
    st.caption(f"API Endpoint: {API_URL}")
    
    render_health_indicator()
    st.divider()
    render_node_list()
    st.divider()
    render_registration_form()
    st.divider()
    render_delete_button()


if __name__ == "__main__":
    main()
