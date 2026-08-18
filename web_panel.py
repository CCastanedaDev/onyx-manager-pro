import os
import sys
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
from datetime import datetime

# Añadir el directorio raíz al PATH para poder importar los módulos de src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.logic.stats_shop import StatsShop, SKILLS_DISPONIBLES, ATRIBUTOS_DISPONIBLES

app = Flask(__name__)
app.secret_key = "onyx_manager_pro_secret_key_12345"

# Configuración de rutas por defecto (se pueden personalizar)
DB_PATH = r"Y:\scum_server\SCUM\Saved\SaveFiles\SCUM.db"
DATA_DIR = r"Y:\data"

# Inicializar StatsShop
stats_shop = StatsShop(db_path=DB_PATH, data_dir=DATA_DIR)

# Credenciales de acceso
ADMIN_USER = "andes"
ADMIN_PASS = "Aminea10!"

# HTML de la aplicación (Tema Oscuro Premium Ultra con diseño responsivo, badges y AJAX)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ONYX Stats Web Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0a0b0e;
            --bg-panel: #11131a;
            --bg-card: #171b26;
            --accent: #f59e0b;
            --accent-glow: rgba(245, 158, 11, 0.15);
            --text-main: #f3f4f6;
            --text-muted: #8e95a5;
            --success: #10b981;
            --danger: #ef4444;
            --border: #232838;
            --font-main: 'Outfit', sans-serif;
            
            /* Stat Colors */
            --color-str: #ef4444;
            --color-con: #f59e0b;
            --color-dex: #10b981;
            --color-int: #3b82f6;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--font-main);
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(at 0% 0%, rgba(245, 158, 11, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.05) 0px, transparent 50%);
        }

        .db-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 15px;
        }
        .db-status-online {
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .db-status-offline-ready {
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--accent);
            border: 1px solid rgba(245, 158, 11, 0.2);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-dot-online {
            background-color: var(--success);
            box-shadow: 0 0 8px var(--success);
        }
        .status-dot-ready {
            background-color: var(--accent);
            box-shadow: 0 0 8px var(--accent);
        }

        header {
            background-color: rgba(17, 19, 26, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-text {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.5px;
            background: linear-gradient(135deg, var(--accent), #ffc043);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .user-area {
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 14px;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-primary {
            background-color: var(--accent);
            color: #000;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3);
        }

        .btn-primary:hover {
            background-color: #ffb020;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
        }

        .btn-danger {
            background-color: rgba(239, 68, 68, 0.15);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .btn-danger:hover {
            background-color: var(--danger);
            color: #fff;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background-color: #1b1e2a;
            color: var(--text-main);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background-color: #262a3b;
            border-color: #4a5472;
            transform: translateY(-1px);
        }

        .container {
            max-width: 1450px;
            width: 100%;
            margin: 30px auto;
            padding: 0 24px;
            display: grid;
            grid-template-columns: 1fr 1.3fr;
            gap: 30px;
            flex-grow: 1;
        }

        @media (max-width: 1100px) {
            .container {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background-color: var(--bg-panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .panel-title {
            font-size: 19px;
            font-weight: 700;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
            color: var(--text-main);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-title span.title-accent {
            color: var(--accent);
        }

        /* Form Controls */
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        input, select {
            background-color: rgba(10, 11, 14, 0.6);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-main);
            font-size: 14px;
            font-family: inherit;
            width: 100%;
            outline: none;
            transition: all 0.2s ease;
        }

        input:focus, select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
            background-color: rgba(10, 11, 14, 0.9);
        }

        .search-row {
            display: flex;
            gap: 12px;
        }

        .search-results {
            background-color: rgba(10, 11, 14, 0.8);
            border: 1px solid var(--border);
            border-radius: 8px;
            max-height: 180px;
            overflow-y: auto;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
        }

        .search-item {
            padding: 12px 18px;
            cursor: pointer;
            transition: all 0.15s;
            font-size: 13px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .search-item:hover {
            background-color: var(--bg-card);
            color: var(--accent);
            padding-left: 22px;
        }

        .player-badge {
            background-color: rgba(245, 158, 11, 0.03);
            border: 1.5px dashed var(--accent);
            border-radius: 10px;
            padding: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 18px;
        }

        /* Skills Area */
        .skills-manager {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
            background-color: rgba(10, 11, 14, 0.4);
        }

        .skills-actions {
            display: grid;
            grid-template-columns: 2fr 1fr auto auto;
            gap: 12px;
            align-items: flex-end;
            margin-bottom: 18px;
        }

        @media (max-width: 600px) {
            .skills-actions {
                grid-template-columns: 1fr;
            }
        }

        .added-skills-list {
            max-height: 200px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background-color: rgba(0,0,0,0.2);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.03);
        }

        .skill-item {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        /* Subscriptions List */
        .subs-list {
            display: flex;
            flex-direction: column;
            gap: 18px;
            max-height: 800px;
            overflow-y: auto;
            padding-right: 8px;
        }

        .sub-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            position: relative;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .sub-card:hover {
            border-color: rgba(245, 158, 11, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }

        .sub-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .sub-player-name {
            font-weight: 700;
            font-size: 16px;
            color: var(--text-main);
        }

        .sub-steam-id {
            font-size: 12px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
            margin-top: 2px;
        }

        .status-badge {
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 6px;
        }

        .status-activo { background-color: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
        .status-pendiente_aplicar { background-color: rgba(245, 158, 11, 0.15); color: var(--accent); border: 1px solid rgba(245, 158, 11, 0.3); }
        .status-pendiente_restaurar { background-color: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }

        .sub-card-body {
            font-size: 13px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            border-top: 1px solid var(--border);
            padding-top: 15px;
        }

        .sub-date-info {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-muted);
            font-size: 12px;
        }

        /* Attribute Badges */
        .badge-grid-attrs {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin: 4px 0;
        }

        .attr-badge {
            border-radius: 6px;
            padding: 6px 10px;
            text-align: center;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            border: 1px solid rgba(255,255,255,0.03);
        }

        .badge-str { background-color: rgba(239, 68, 68, 0.08); color: var(--color-str); border-color: rgba(239, 68, 68, 0.15); }
        .badge-con { background-color: rgba(245, 158, 11, 0.08); color: var(--color-con); border-color: rgba(245, 158, 11, 0.15); }
        .badge-dex { background-color: rgba(16, 185, 129, 0.08); color: var(--color-dex); border-color: rgba(16, 185, 129, 0.15); }
        .badge-int { background-color: rgba(59, 130, 246, 0.08); color: var(--color-int); border-color: rgba(59, 130, 246, 0.15); }

        /* Skills Badges */
        .skills-badges-area {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 5px;
        }

        .lvl-badge {
            font-size: 10px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            background-color: #242938;
            border: 1px solid var(--border);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .lvl-badge span.lvl-num {
            font-weight: 800;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 9px;
        }

        /* Skill Level Colors */
        .lvl-1 { border-color: #9ca3af; color: #f3f4f6; } /* Básico */
        .lvl-1 span.lvl-num { background-color: #4b5563; }
        .lvl-2 { border-color: #3b82f6; color: #93c5fd; } /* Medio */
        .lvl-2 span.lvl-num { background-color: #2563eb; }
        .lvl-3 { border-color: #8b5cf6; color: #c084fc; } /* Avanzado */
        .lvl-3 span.lvl-num { background-color: #7c3aed; }
        .lvl-4 { border-color: #f59e0b; color: #fde047; box-shadow: 0 0 5px rgba(245, 158, 11, 0.2); } /* Avanzado+ */
        .lvl-4 span.lvl-num { background-color: #d97706; }
        .lvl-5 { border-color: #ef4444; color: #fca5a5; box-shadow: 0 0 8px rgba(239, 68, 68, 0.3); } /* Máximo */
        .lvl-5 span.lvl-num { background-color: #dc2626; }

        .sub-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            border-top: 1px solid var(--border);
            padding-top: 15px;
            margin-top: 5px;
        }

        .filter-bar input {
            background-color: var(--bg-card);
            border-color: var(--border);
        }

        /* Scrollbars Custom */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-main);
        }

        ::-webkit-scrollbar-thumb {
            background: #2e3446;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #414a63;
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background-color: var(--bg-panel);
            border: 1px solid var(--border);
            border-left: 5px solid var(--accent);
            padding: 16px 28px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
            display: none;
            z-index: 1000;
            animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            font-weight: 500;
            font-size: 14px;
        }

        @keyframes slideIn {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <span class="logo-text">ONYX STATS WEB PANEL</span>
        </div>
        <div class="user-area">
            <div id="dbStatusBadge" class="db-status-badge db-status-online">
                <span id="dbStatusDot" class="status-dot status-dot-online"></span>
                <span id="dbStatusText">Cargando Estado...</span>
            </div>
            <span>Sesión iniciada como <strong>{{ session.username }}</strong></span>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Cerrar Sesión</a>
        </div>
    </header>

    <div class="container">
        <!-- Panel Izquierdo: Formularios -->
        <div class="panel">
            <div class="panel-title">1. Seleccionar Jugador</div>
            
            <div class="search-row">
                <input type="text" id="playerSearchInput" placeholder="Buscar por nombre o SteamID...">
                <button class="btn btn-primary" onclick="searchPlayers()">Buscar</button>
            </div>
            
            <div class="search-results" id="searchResults" style="display: none;"></div>
            
            <div class="player-badge" id="selectedPlayerBadge">
                <div style="color: var(--text-muted); font-style: italic;">Ningún jugador seleccionado</div>
            </div>

            <!-- Atributos -->
            <div class="panel-title">2. Asignar Atributos <span class="title-accent">(Stats)</span></div>
            <div class="stats-grid">
                <div class="form-group">
                    <label style="color: var(--color-str);">Fuerza (STR)</label>
                    <input type="number" step="0.1" id="strInput" placeholder="0 - 5.0">
                </div>
                <div class="form-group">
                    <label style="color: var(--color-con);">Constitución (CON)</label>
                    <input type="number" step="0.1" id="conInput" placeholder="0 - 5.0">
                </div>
                <div class="form-group">
                    <label style="color: var(--color-dex);">Destreza (DEX)</label>
                    <input type="number" step="0.1" id="dexInput" placeholder="0 - 5.0">
                </div>
                <div class="form-group">
                    <label style="color: var(--color-int);">Inteligencia (INT)</label>
                    <input type="number" step="0.1" id="intInput" placeholder="0 - 5.0">
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-end; gap: 15px;">
                <div class="form-group" style="width: 130px;">
                    <label>Duración (Días)</label>
                    <input type="number" id="attrDaysInput" value="30">
                </div>
                <button class="btn btn-primary" onclick="saveAttributes()">Guardar Atributos</button>
            </div>

            <!-- Habilidades -->
            <div class="panel-title">3. Asignar Habilidades <span class="title-accent">(Skills)</span></div>
            <div class="skills-manager">
                <div class="skills-actions">
                    <div class="form-group">
                        <label>Habilidad</label>
                        <select id="skillSelect">
                            {% for skill in skills %}
                            <option value="{{ skill }}">{{ skill }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Nivel</label>
                        <select id="skillLevelInput" style="padding: 11px 10px;">
                            <option value="1">Básico (1)</option>
                            <option value="2">Medio (2)</option>
                            <option value="3" selected>Avanzado (3)</option>
                            <option value="4">Avanzado+ (4)</option>
                            <option value="5">Máximo (5)</option>
                        </select>
                    </div>
                    <button class="btn btn-secondary" onclick="addSkillToList()">Agregar</button>
                    <button class="btn btn-secondary" style="background-color: #2563eb; border-color: #3b82f6; color: white;" onclick="addAllSkillsToList()">Max Todos</button>
                </div>
                <div class="added-skills-list" id="addedSkillsList">
                    <div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 15px; font-style: italic;">Ningún skill agregado a la lista</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-end; gap: 15px;">
                <div class="form-group" style="width: 130px;">
                    <label>Duración (Días)</label>
                    <input type="number" id="skillsDaysInput" value="30">
                </div>
                <button class="btn btn-primary" onclick="saveSkills()">Guardar Habilidades</button>
            </div>
        </div>

        <!-- Panel Derecho: Suscripciones Activas -->
        <div class="panel">
            <div class="panel-title">
                Suscripciones Activas / Pendientes
                <span class="status-badge" style="background-color: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border);" id="subCount">Cargando...</span>
            </div>
            <div id="applyPendingContainer" style="display: none; background-color: rgba(245, 158, 11, 0.05); border: 1px dashed var(--accent); padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; gap: 15px;">
                <div style="font-size: 13px;">
                    <span style="color: var(--accent); font-weight: 700; display: block; margin-bottom: 2px;">⚡ CAMBIOS PENDIENTES</span>
                    Hay suscripciones/skills esperando a ser aplicados a la base de datos.
                </div>
                <button class="btn btn-primary" id="btnApplyPending" onclick="applyPendingChanges()" style="padding: 8px 16px; font-size: 12px; white-space: nowrap;">Aplicar Ahora</button>
            </div>
            <div class="filter-bar">
                <input type="text" id="subFilterInput" placeholder="Filtrar suscripciones por nombre o SteamID..." onkeyup="filterSubscriptions()">
            </div>
            <div class="subs-list" id="subsContainer">
                <div style="text-align: center; color: var(--text-muted); padding: 50px; font-style: italic;">Cargando suscripciones activas...</div>
            </div>
        </div>
    </div>

    <div class="toast" id="toast">Mensaje aquí</div>

    <script>
        let selectedPlayer = null;
        let skillsPackage = {};
        const availableSkills = {{ skills|tojson }};

        // Al iniciar, cargar suscripciones y verificar estado de la base de datos
        document.addEventListener("DOMContentLoaded", () => {
            loadSubscriptions();
            checkDbStatus();
            setInterval(checkDbStatus, 8000); // Verificar cada 8 segundos
        });

        function checkDbStatus() {
            fetch('/api/db_status')
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById("dbStatusBadge");
                    const dot = document.getElementById("dbStatusDot");
                    const text = document.getElementById("dbStatusText");
                    const applyContainer = document.getElementById("applyPendingContainer");
                    const applyBtn = document.getElementById("btnApplyPending");

                    if (data.locked) {
                        // Servidor online (base de datos bloqueada)
                        badge.className = "db-status-badge db-status-online";
                        dot.className = "status-dot status-dot-online";
                        text.innerText = "Servidor Online (Lectura)";
                        
                        if (applyBtn) {
                            applyBtn.disabled = true;
                            applyBtn.innerText = "Servidor Online";
                            applyBtn.style.opacity = "0.6";
                            applyBtn.title = "La base de datos está bloqueada por el proceso del servidor SCUM. Apágalo para aplicar cambios.";
                        }
                    } else {
                        // Servidor offline (base de datos desbloqueada)
                        badge.className = "db-status-badge db-status-offline-ready";
                        dot.className = "status-dot status-dot-ready";
                        text.innerText = "Servidor Offline (Escritura)";

                        if (applyBtn) {
                            applyBtn.disabled = false;
                            applyBtn.innerText = "Aplicar Ahora";
                            applyBtn.style.opacity = "1";
                            applyBtn.title = "Aplica todos los cambios pendientes inmediatamente a SCUM.db";
                        }
                    }

                    if (data.pending_count > 0) {
                        applyContainer.style.display = "flex";
                    } else {
                        applyContainer.style.display = "none";
                    }
                })
                .catch(err => console.error("Error al obtener estado de DB:", err));
        }

        function applyPendingChanges() {
            const btn = document.getElementById("btnApplyPending");
            btn.disabled = true;
            btn.innerText = "Aplicando...";
            
            fetch('/api/apply_pending', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast(data.message);
                        loadSubscriptions();
                        checkDbStatus();
                    } else {
                        showToast(data.message, true);
                        checkDbStatus();
                    }
                })
                .catch(err => {
                    showToast("Error al conectar con la API", true);
                    checkDbStatus();
                });
        }

        function showToast(message, isError = false) {
            const toast = document.getElementById("toast");
            toast.innerText = message;
            toast.style.borderLeftColor = isError ? "var(--danger)" : "var(--success)";
            toast.style.display = "block";
            setTimeout(() => {
                toast.style.display = "none";
            }, 3500);
        }

        function searchPlayers() {
            const query = document.getElementById("playerSearchInput").value.trim();
            if (!query) return;

            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const resultsDiv = document.getElementById("searchResults");
                    resultsDiv.innerHTML = "";
                    if (data.length === 0) {
                        resultsDiv.innerHTML = '<div class="search-item" style="color: var(--danger);">No se encontraron jugadores</div>';
                        resultsDiv.style.display = "block";
                        return;
                    }

                    data.forEach(p => {
                        const item = document.createElement("div");
                        item.className = "search-item";
                        item.innerHTML = `<span><strong>${p.name}</strong> (${p.steam_id})</span><span>Fama: ${p.fame}</span>`;
                        item.onclick = () => selectPlayer(p);
                        resultsDiv.appendChild(item);
                    });
                    resultsDiv.style.display = "block";
                })
                .catch(err => showToast("Error buscando jugadores", true));
        }

        function selectPlayer(p) {
            selectedPlayer = p;
            document.getElementById("searchResults").style.display = "none";
            document.getElementById("selectedPlayerBadge").innerHTML = `
                <div>
                    <div style="font-weight: 700; font-size: 15px; color: var(--accent);">${p.name}</div>
                    <div style="font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-top: 2px;">${p.steam_id}</div>
                </div>
                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 11px;" onclick="clearSelectedPlayer()">Desmarcar</button>
            `;
            showToast(`Jugador seleccionado: ${p.name}`);
        }

        function clearSelectedPlayer() {
            selectedPlayer = null;
            document.getElementById("selectedPlayerBadge").innerHTML = `<div style="color: var(--text-muted); font-style: italic;">Ningún jugador seleccionado</div>`;
        }

        function addSkillToList() {
            const skill = document.getElementById("skillSelect").value;
            const level = parseInt(document.getElementById("skillLevelInput").value);
            if (!skill || isNaN(level)) return;

            skillsPackage[skill] = level;
            renderAddedSkills();
        }

        function addAllSkillsToList() {
            const level = parseInt(document.getElementById("skillLevelInput").value) || 3;
            availableSkills.forEach(skill => {
                skillsPackage[skill] = level;
            });
            renderAddedSkills();
            showToast(`Se agregaron todos los skills con nivel ${level}`);
        }

        function removeSkillFromList(skill) {
            delete skillsPackage[skill];
            renderAddedSkills();
        }

        function renderAddedSkills() {
            const listDiv = document.getElementById("addedSkillsList");
            listDiv.innerHTML = "";
            const keys = Object.keys(skillsPackage);
            if (keys.length === 0) {
                listDiv.innerHTML = '<div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 15px; font-style: italic;">Ningún skill agregado a la lista</div>';
                return;
            }

            keys.forEach(skill => {
                const item = document.createElement("div");
                item.className = "skill-item";
                item.innerHTML = `
                    <span><strong>${skill}</strong></span>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="lvl-badge lvl-${skillsPackage[skill]}"><span class="lvl-num">${skillsPackage[skill]}</span></span>
                        <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="removeSkillFromList('${skill}')">Eliminar</button>
                    </div>
                `;
                listDiv.appendChild(item);
            });
        }

        function saveAttributes() {
            if (!selectedPlayer) {
                showToast("Por favor selecciona un jugador primero", true);
                return;
            }

            const strVal = parseFloat(document.getElementById("strInput").value) || 0;
            const conVal = parseFloat(document.getElementById("conInput").value) || 0;
            const dexVal = parseFloat(document.getElementById("dexInput").value) || 0;
            const intVal = parseFloat(document.getElementById("intInput").value) || 0;
            const days = parseInt(document.getElementById("attrDaysInput").value) || 30;

            if (strVal === 0 && conVal === 0 && dexVal === 0 && intVal === 0) {
                showToast("Introduce al menos un atributo mayor a 0", true);
                return;
            }

            const payload = {
                steam_id: selectedPlayer.steam_id,
                player_name: selectedPlayer.name,
                prisoner_id: selectedPlayer.prisoner_id,
                dias: days,
                atributos: { Strength: strVal, Constitution: conVal, Dexterity: dexVal, Intelligence: intVal }
            };

            fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast("Atributos guardados. Se aplicarán en el próximo reinicio.");
                    loadSubscriptions();
                } else {
                    showToast("Error al guardar atributos: " + data.message, true);
                }
            });
        }

        function saveSkills() {
            if (!selectedPlayer) {
                showToast("Por favor selecciona un jugador primero", true);
                return;
            }

            const days = parseInt(document.getElementById("skillsDaysInput").value) || 30;
            if (Object.keys(skillsPackage).length === 0) {
                showToast("Agrega al menos una habilidad a la lista", true);
                return;
            }

            const payload = {
                steam_id: selectedPlayer.steam_id,
                player_name: selectedPlayer.name,
                prisoner_id: selectedPlayer.prisoner_id,
                dias: days,
                skills: skillsPackage
            };

            fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast("Habilidades guardadas. Se aplicarán en el próximo reinicio.");
                    skillsPackage = {};
                    renderAddedSkills();
                    loadSubscriptions();
                } else {
                    showToast("Error al guardar habilidades: " + data.message, true);
                }
            });
        }

        function loadSubscriptions() {
            fetch('/api/subscriptions')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById("subsContainer");
                    container.innerHTML = "";
                    document.getElementById("subCount").innerText = `${data.length} Activas/Pendientes`;
                    
                    if (data.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 50px; font-style: italic;">No hay suscripciones activas</div>';
                        return;
                    }

                    data.forEach(sub => {
                        const card = document.createElement("div");
                        card.className = "sub-card";
                        card.dataset.name = sub.player_name.toLowerCase();
                        card.dataset.steam = sub.steam_id;

                        // Formatear atributos redondeados a 2 decimales
                        let attrsHtml = "";
                        if (sub.atributos_nuevos) {
                            attrsHtml = `
                                <div class="badge-grid-attrs">
                                    <div class="attr-badge badge-str"><span>STR</span><strong>${parseFloat(sub.atributos_nuevos.Strength || 0).toFixed(2)}</strong></div>
                                    <div class="attr-badge badge-con"><span>CON</span><strong>${parseFloat(sub.atributos_nuevos.Constitution || 0).toFixed(2)}</strong></div>
                                    <div class="attr-badge badge-dex"><span>DEX</span><strong>${parseFloat(sub.atributos_nuevos.Dexterity || 0).toFixed(2)}</strong></div>
                                    <div class="attr-badge badge-int"><span>INT</span><strong>${parseFloat(sub.atributos_nuevos.Intelligence || 0).toFixed(2)}</strong></div>
                                </div>
                            `;
                        } else {
                            attrsHtml = `<span style="color: var(--text-muted); font-style: italic;">Ninguno</span>`;
                        }

                        // Formatear skills
                        let skillsHtml = "";
                        if (sub.skills_nuevos && Object.keys(sub.skills_nuevos).length > 0) {
                            const badges = Object.entries(sub.skills_nuevos)
                                .map(([k, v]) => `
                                    <span class="lvl-badge lvl-${v}">
                                        <strong>${k.replace('Skill', '')}</strong>
                                        <span class="lvl-num">${v}</span>
                                    </span>
                                `)
                                .join("");
                            skillsHtml = `<div class="skills-badges-area">${badges}</div>`;
                        } else {
                            skillsHtml = `<span style="color: var(--text-muted); font-style: italic;">Ninguno</span>`;
                        }

                        card.innerHTML = `
                            <div class="sub-card-header">
                                <div>
                                    <div class="sub-player-name">${sub.player_name}</div>
                                    <div class="sub-steam-id">${sub.steam_id}</div>
                                </div>
                                <span class="status-badge status-${sub.estado}">${sub.estado.replace('_', ' ')}</span>
                            </div>
                            <div class="sub-card-body">
                                <div class="sub-date-info">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                    <span>Expira el: <strong>${sub.fecha_expiracion}</strong></span>
                                </div>
                                <div style="margin-top: 5px;">
                                    <label>Atributos</label>
                                    ${attrsHtml}
                                </div>
                                <div style="margin-top: 5px;">
                                    <label>Habilidades</label>
                                    ${skillsHtml}
                                </div>
                            </div>
                            <div class="sub-actions">
                                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 11px;" onclick="editSubscription(${JSON.stringify(sub).replace(/"/g, '&quot;')})">Editar</button>
                                <button class="btn btn-danger" style="padding: 6px 12px; font-size: 11px;" onclick="revokeSubscription('${sub.steam_id}')">Revocar</button>
                            </div>
                        `;
                        container.appendChild(card);
                    });
                });
        }

        function filterSubscriptions() {
            const filterVal = document.getElementById("subFilterInput").value.toLowerCase();
            const cards = document.querySelectorAll(".sub-card");
            cards.forEach(card => {
                const name = card.dataset.name;
                const steam = card.dataset.steam;
                if (name.includes(filterVal) || steam.includes(filterVal)) {
                    card.style.display = "flex";
                } else {
                    card.style.display = "none";
                }
            });
        }

        function revokeSubscription(steamId) {
            if (!confirm("¿Estás seguro de que deseas revocar los beneficios de este jugador?")) return;

            fetch(`/api/revoke/${steamId}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast("Beneficios revocados con éxito.");
                        loadSubscriptions();
                    } else {
                        showToast("Error al revocar beneficios", true);
                    }
                });
        }

        function editSubscription(sub) {
            // Seleccionar jugador
            selectPlayer({
                steam_id: sub.steam_id,
                name: sub.player_name,
                prisoner_id: sub.prisoner_id,
                fame: 0
            });

            // Rellenar campos de atributos si existen (redondeados para edición limpia)
            if (sub.atributos_nuevos) {
                document.getElementById("strInput").value = parseFloat(sub.atributos_nuevos.Strength || 0).toFixed(2);
                document.getElementById("conInput").value = parseFloat(sub.atributos_nuevos.Constitution || 0).toFixed(2);
                document.getElementById("dexInput").value = parseFloat(sub.atributos_nuevos.Dexterity || 0).toFixed(2);
                document.getElementById("intInput").value = parseFloat(sub.atributos_nuevos.Intelligence || 0).toFixed(2);
            } else {
                document.getElementById("strInput").value = "";
                document.getElementById("conInput").value = "";
                document.getElementById("dexInput").value = "";
                document.getElementById("intInput").value = "";
            }

            // Rellenar lista de skills si existen
            skillsPackage = {};
            if (sub.skills_nuevos) {
                Object.assign(skillsPackage, sub.skills_nuevos);
            }
            renderAddedSkills();

            showToast(`Cargados datos de ${sub.player_name} para edición`);
        }
    </script>
</body>
</html>
"""

# HTML del Login Screen
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - ONYX Stats</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #0a0b0e;
            color: #f3f4f6;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-image: radial-gradient(circle at center, rgba(245, 158, 11, 0.05) 0px, transparent 60%);
        }
        .login-card {
            background-color: #11131a;
            border: 1px solid #232838;
            border-radius: 16px;
            padding: 45px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        h2 {
            text-align: center;
            color: #f59e0b;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        label {
            font-size: 12px;
            font-weight: 600;
            color: #8e95a5;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        input {
            background-color: #0a0b0e;
            border: 1px solid #232838;
            border-radius: 8px;
            padding: 14px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        input:focus {
            border-color: #f59e0b;
            box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
        }
        .btn {
            background-color: #f59e0b;
            color: #000;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 10px;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.2);
        }
        .btn:hover {
            background-color: #ffb020;
            transform: translateY(-1px);
        }
        .error-msg {
            color: #ef4444;
            font-size: 13px;
            text-align: center;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>ONYX STATS LOGIN</h2>
        {% if error %}
        <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Usuario</label>
                <input type="text" name="username" required>
            </div>
            <div style="height: 10px;"></div>
            <div class="form-group">
                <label>Contraseña</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">Iniciar Sesión</button>
        </form>
    </div>
</body>
</html>
"""

# Middleware de Autenticación
def login_required(f):
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Usuario o contraseña incorrectos")
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    return render_template_string(
        HTML_TEMPLATE, 
        skills=SKILLS_DISPONIBLES, 
        atributos=ATRIBUTOS_DISPONIBLES
    )

# --- ENDPOINTS API ---

@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    results = stats_shop.buscar_jugadores(query)
    return jsonify(results)

@app.route("/api/subscriptions")
@login_required
def api_subscriptions():
    subs = stats_shop.obtener_subs_activas()
    return jsonify(subs)

@app.route("/api/register", methods=["POST"])
@login_required
def api_register():
    data = request.json
    steam_id = data.get("steam_id")
    player_name = data.get("player_name")
    prisoner_id = data.get("prisoner_id")
    dias = int(data.get("dias", 30))
    atributos = data.get("atributos")
    skills = data.get("skills")

    # Limpiar atributos si están todos en 0
    if atributos:
        has_vals = any(v > 0 for v in atributos.values())
        if not has_vals:
            atributos = None

    success = stats_shop.registrar_pack(
        steam_id=steam_id,
        player_name=player_name,
        prisoner_id=prisoner_id,
        dias=dias,
        atributos=atributos,
        skills=skills
    )

    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "No se pudo registrar en JSON"})

@app.route("/api/revoke/<steam_id>", methods=["POST"])
@login_required
def api_revoke(steam_id):
    success = stats_shop.revocar_pack(steam_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/api/db_status")
@login_required
def api_db_status():
    locked = stats_shop.db_esta_bloqueada()
    stats_shop._subs = stats_shop._cargar_subs()
    pending = [s for s in stats_shop._subs if s["estado"] in ("pendiente_aplicar", "pendiente_restaurar")]
    return jsonify({
        "locked": locked,
        "pending_count": len(pending)
    })

@app.route("/api/apply_pending", methods=["POST"])
@login_required
def api_apply_pending():
    stats_shop._subs = stats_shop._cargar_subs()
    pendientes = [s for s in stats_shop._subs if s["estado"] in ("pendiente_aplicar", "pendiente_restaurar")]
    if not pendientes:
        return jsonify({"success": False, "message": "No hay cambios pendientes por aplicar."})
        
    if stats_shop.db_esta_bloqueada():
        return jsonify({
            "success": False, 
            "message": "La base de datos está bloqueada (el servidor está online). Detén o reinicia el servidor para poder aplicar los cambios."
        })
        
    try:
        stats_shop.verificar_vencimientos()
        stats_shop.ejecutar_pendientes()
        return jsonify({"success": True, "message": "Todos los cambios pendientes fueron aplicados correctamente a la base de datos."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error al aplicar cambios: {str(e)}"})

# --- HILO MONITOR DE REINICIOS ---
import time
import threading

def background_db_monitor():
    print("🚀 [StatsShop Monitor] Iniciando monitor en segundo plano para aplicar cambios post-reinicio...", flush=True)
    while True:
        try:
            # Recargar de disco las suscripciones
            stats_shop._subs = stats_shop._cargar_subs()
            pendientes = [s for s in stats_shop._subs if s["estado"] in ("pendiente_aplicar", "pendiente_restaurar")]
            if pendientes:
                # Comprobar si la base de datos se liberó (el servidor SCUM se apagó o reinició)
                if not stats_shop.db_esta_bloqueada():
                    print("⚡ [StatsShop Monitor] ¡Base de datos desbloqueada detectada con cambios pendientes! Aplicando...", flush=True)
                    try:
                        stats_shop.verificar_vencimientos()
                        stats_shop.ejecutar_pendientes()
                        print("✅ [StatsShop Monitor] Cambios pendientes aplicados automáticamente con éxito.", flush=True)
                    except Exception as e:
                        print(f"❌ [StatsShop Monitor] Error aplicando automáticamente: {e}", flush=True)
        except Exception as e:
            print(f"⚠️ [StatsShop Monitor] Error en bucle del monitor: {e}", flush=True)
        
        # Revisar cada 15 segundos
        time.sleep(15)

# Iniciar el hilo monitor
t = threading.Thread(target=background_db_monitor, daemon=True)
t.start()

if __name__ == "__main__":
    # Iniciar en puerto 5000 expuesto localmente
    app.run(host="0.0.0.0", port=5000, debug=False)
