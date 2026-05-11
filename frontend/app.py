import os
import requests as req
from flask import Flask, Response, request
 
BACKEND_URL = os.environ.get("API_URL", "http://api:8080")
REQUEST_TIMEOUT = 8
 
app = Flask(__name__)
 
 
def fetch_health():
    try:
        r = req.get(f"{BACKEND_URL}/health", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"error": True}
 
 
def fetch_nodes():
    try:
        r = req.get(f"{BACKEND_URL}/api/nodes", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []
 
 
def render_page(message: str = "", error: str = "") -> str:
    health = fetch_health()
    nodes = fetch_nodes()
 
    if "error" in health:
        health_html = '<p class="error">Backend: OFFLINE</p>'
    else:
        status = health.get("status", "unknown")
        db = health.get("db", "unknown")
        count = health.get("nodes_count", 0)
        color = "green" if status == "ok" and db == "connected" else "orange"
        health_html = f"""
        <p style="color:{color}">
            Backend: {'ONLINE' if status == 'ok' else 'UNHEALTHY'} |
            DB: {db.upper()} |
            Active nodes: {count}
        </p>"""
 
    rows = ""
    for n in nodes:
        rows += (
            f"<tr><td>{n.get('name','')}</td><td>{n.get('host','')}</td>"
            f"<td>{n.get('port','')}</td><td>{n.get('status','')}</td></tr>"
        )
 
    nodes_table = f"""
    <table border="1" cellpadding="6" cellspacing="0">
      <thead>
        <tr>
          <th>Node Name</th><th>Host Address</th>
          <th>Port Number</th><th>Current Status</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="4">No nodes registered yet</td></tr>'}
      </tbody>
    </table>"""
 
    msg_html = f'<p class="success">{message}</p>' if message else ""
    err_html = f'<p class="error">{error}</p>' if error else ""
 
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Node Registry Dashboard</title>
  <style>
    body {{ font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ color: #333; }}
    h2 {{ margin-top: 30px; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ background: #f0f0f0; }}
    .success {{ color: green; font-weight: bold; }}
    .error {{ color: red; font-weight: bold; }}
    input, select {{ padding: 6px; margin: 4px 0; width: 100%; box-sizing: border-box; }}
    button {{ padding: 8px 16px; background: #0066cc; color: white; border: none;
             cursor: pointer; border-radius: 4px; margin-top: 8px; }}
    button:hover {{ background: #0052a3; }}
    .delete-btn {{ background: #cc3300; }}
    .delete-btn:hover {{ background: #a32800; }}
    form {{ max-width: 400px; }}
    label {{ display: block; margin-top: 10px; font-weight: bold; }}
    hr {{ margin: 30px 0; }}
  </style>
</head>
<body>
  <h1>🖥️ Node Registry Dashboard</h1>
  <p><small>Connected to backend: {BACKEND_URL}</small></p>
 
  <h2>Health Status</h2>
  {health_html}
  <hr/>
 
  <h2>Registered Nodes Inventory</h2>
  {nodes_table}
  <hr/>
 
  <h2>Register New Node</h2>
  {msg_html}{err_html}
  <form method="POST" action="/register">
    <label for="name">Node Name</label>
    <input id="name" name="name" type="text" placeholder="e.g., primary-worker-01" required/>
    <label for="host">Host Address</label>
    <input id="host" name="host" type="text" placeholder="e.g., 10.0.1.100" required/>
    <label for="port">Port</label>
    <input id="port" name="port" type="number" min="1" max="65535" value="8080" required/>
    <button type="submit">Add Node to Registry</button>
  </form>
  <hr/>
 
  <h2>Remove Node (Soft Delete)</h2>
  <p><small>Marks the node as inactive — not a permanent removal.</small></p>
  <form method="POST" action="/delete">
    <label for="del_name">Node Name to Delete</label>
    <input id="del_name" name="name" type="text" placeholder="Enter exact node name" required/>
    <button type="submit" class="delete-btn">Mark Node as Inactive</button>
  </form>
</body>
</html>"""
 
 
@app.route("/", methods=["GET"])
def index():
    return Response(render_page(), mimetype="text/html")
 
 
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    host = request.form.get("host", "").strip()
    port = request.form.get("port", "8080").strip()
 
    if not name or not host:
        return Response(render_page(error="Node Name and Host Address are required"), mimetype="text/html")
 
    try:
        port_int = int(port)
    except ValueError:
        return Response(render_page(error="Invalid port number"), mimetype="text/html")
 
    try:
        resp = req.post(
            f"{BACKEND_URL}/api/nodes",
            json={"name": name, "host": host, "port": port_int},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 201:
            return Response(render_page(message=f"Node '{name}' successfully registered!"), mimetype="text/html")
        elif resp.status_code == 409:
            detail = resp.json().get("detail", "Node already exists")
            return Response(render_page(error=f"Conflict: {detail}"), mimetype="text/html")
        else:
            detail = resp.json().get("detail", f"HTTP {resp.status_code}")
            return Response(render_page(error=f"Registration failed: {detail}"), mimetype="text/html")
    except Exception as e:
        return Response(render_page(error=f"Connection failed: {e}"), mimetype="text/html")
 
 
@app.route("/delete", methods=["POST"])
def delete():
    name = request.form.get("name", "").strip()
    if not name:
        return Response(render_page(error="Please provide a node name"), mimetype="text/html")
 
    try:
        resp = req.delete(f"{BACKEND_URL}/api/nodes/{name}", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 204:
            return Response(render_page(message=f"Node '{name}' deactivated (soft-deleted)"), mimetype="text/html")
        elif resp.status_code == 404:
            detail = resp.json().get("detail", "Node not found")
            return Response(render_page(error=f"Not Found: {detail}"), mimetype="text/html")
        else:
            detail = resp.json().get("detail", f"HTTP {resp.status_code}")
            return Response(render_page(error=f"Deletion failed: {detail}"), mimetype="text/html")
    except Exception as e:
        return Response(render_page(error=f"Connection failed: {e}"), mimetype="text/html")
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False)