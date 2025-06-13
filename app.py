from flask import Flask, request, jsonify, render_template
import json
import os
import requests

app = Flask(__name__)

ACCOUNT_ID = "2e2ff7ceef83c761f6b55bf619835c7a"
AUTH_TOKEN = "LtPUuT9fcVzc3xfOZG8gkckK5diUh7EmKPyrhIXR"

RUTA_CONFIGURACION = os.path.join("configuracion_prompts", "configuracion_total.json")
os.makedirs("configuracion_prompts", exist_ok=True)

def cargar_config():
    if not os.path.exists(RUTA_CONFIGURACION):
        estructura_inicial = {
            "negocio": {
                "nombre": "Mi Negocio",
                "usuario": "admin",
                "contrasena": "1234",
                "configuracion": {
                    "general": {"content": ""},
                    "negocio": {"content": ""},
                    "reglas": {"content": ""},
                    "actitudes": {}
                }
            }
        }
        with open(RUTA_CONFIGURACION, "w", encoding="utf-8") as f:
            json.dump(estructura_inicial, f, indent=4, ensure_ascii=False)
    with open(RUTA_CONFIGURACION, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_config(data):
    with open(RUTA_CONFIGURACION, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/cliente")
def cliente():
    return render_template("cliente.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/navbar")
def navbar():
    return render_template("navbar_usuario.html")

# ---------------------- API de actitudes ----------------------

@app.route("/get_attitudes")
def get_attitudes():
    data = cargar_config()
    actitudes = data["negocio"]["configuracion"].get("actitudes", {})
    return jsonify(actitudes)

@app.route("/save_attitude", methods=["POST"])
def save_attitude():
    req = request.get_json()
    old_name = req.get("old_name")
    name = req.get("name")
    desc = req.get("desc")

    data = cargar_config()
    actitudes = data["negocio"]["configuracion"].get("actitudes", {})

    if old_name and old_name != name and old_name in actitudes:
        del actitudes[old_name]

    actitudes[name] = desc
    data["negocio"]["configuracion"]["actitudes"] = actitudes
    guardar_config(data)
    return "ok"

@app.route("/delete_attitude", methods=["POST"])
def delete_attitude():
    req = request.get_json()
    name = req.get("name")

    data = cargar_config()
    actitudes = data["negocio"]["configuracion"].get("actitudes", {})
    if name in actitudes:
        del actitudes[name]
        data["negocio"]["configuracion"]["actitudes"] = actitudes
        guardar_config(data)
    return "ok"

@app.route("/save_cliente", methods=["POST"])
def save_cliente():
    req = request.get_json()
    data = cargar_config()
    data["negocio"]["configuracion"]["negocio"]["content"] = req.get("negocio", "")
    data["negocio"]["configuracion"]["reglas"]["content"] = req.get("reglas", "")
    guardar_config(data)
    return "ok"

@app.route("/save_admin", methods=["POST"])
def save_admin():
    req = request.get_json()
    data = cargar_config()
    data["negocio"]["configuracion"]["general"]["content"] = req.get("general", "")
    guardar_config(data)
    return "ok"

@app.route("/load_config")
def load_config():
    data = cargar_config()
    config = data["negocio"]["configuracion"]
    return jsonify({
        "negocio": config.get("negocio", {}).get("content", ""),
        "reglas": config.get("reglas", {}).get("content", ""),
        "general": config.get("general", {}).get("content", "")
    })
@app.route("/get_business_name")
def get_business_name():
    data = cargar_config()
    nombre = data.get("negocio", {}).get("nombre", "Nombre no configurado")
    return jsonify({"nombre": nombre})
@app.route("/send", methods=["POST"])
def send():
    req = request.get_json()
    mensaje_usuario = req.get("message", "")
    actitud_clave = req.get("attitude", "")

    data = cargar_config()
    config = data["negocio"]["configuracion"]

    general = config.get("general", {}).get("content", "")
    negocio = config.get("negocio", {}).get("content", "")
    reglas = config.get("reglas", {}).get("content", "")
    actitudes = config.get("actitudes", {})
    actitud = actitudes.get(actitud_clave, "")

    mensajes = [
        {"role": "system", "content": f"{general}\n\n{negocio}\n\n{actitud}\n\n{reglas}"},
        {"role": "user", "content": mensaje_usuario}
    ]

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"messages": mensajes}
        )
        response_data = response.json()

        if response.status_code == 200:
            respuesta = response_data['result']['response']
            return jsonify({"response": respuesta})
        else:
            return jsonify({"response": f"[Error]: {response_data.get('error', 'Unknown error')}"}), 400
    except Exception as e:
        return jsonify({"response": f"[Error]: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
