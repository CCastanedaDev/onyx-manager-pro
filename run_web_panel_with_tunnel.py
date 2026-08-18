import os
import sys
import time
import socket
import threading
import paramiko

# Parámetros del VPS
VPS_IP = "192.168.1.5"
VPS_PORT = 22
VPS_USER = "rerree"
VPS_PASS = "189981"

# Puertos
PORT_REMOTE = 5001 # Puerto en el VPS
PORT_LOCAL = 5000  # Puerto de Flask local

def run_flask():
    """Inicia la aplicación de Flask directamente en el hilo."""
    print("[FLASK] Iniciando panel web ONYX...", flush=True)
    # Importar el app desde web_panel.py
    from web_panel import app
    # Desactivar debug y reloader para que corra limpiamente en segundo plano
    app.run(host="0.0.0.0", port=PORT_LOCAL, debug=False, use_reloader=False, threaded=True)

def pipe_sockets(src, dst):
    """Reenvía datos de un socket/canal a otro de forma bidireccional y síncrona."""
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.close()
        except:
            pass
        try:
            dst.close()
        except:
            pass

def reverse_forward_handler(chan, host, port):
    """Maneja las conexiones entrantes desde el VPS y las reenvía a Flask local usando hilos bidireccionales."""
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"[ERROR] Al conectar a Flask local en {host}:{port}: {e}", flush=True)
        chan.close()
        return

    print(f"[CONN] Conexion establecida desde el VPS hacia Flask local ({host}:{port})", flush=True)
    
    # Crear dos hilos dedicados para mover los datos (100% compatible con Windows)
    t1 = threading.Thread(target=pipe_sockets, args=(chan, sock))
    t2 = threading.Thread(target=pipe_sockets, args=(sock, chan))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

def ssh_tunnel_loop():
    """Mantiene activa la conexión SSH y el reenvío de puerto inverso."""
    while True:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            print(f"[SSH] Conectando al VPS {VPS_IP}...", flush=True)
            client.connect(
                VPS_IP,
                port=VPS_PORT,
                username=VPS_USER,
                password=VPS_PASS,
                timeout=15
            )
            print("[SSH] Conexion SSH establecida.", flush=True)
            
            transport = client.get_transport()
            # Configurar keepalive en el transporte
            if transport:
                transport.set_keepalive(10)
                # Solicitar el puerto remoto inverso
                transport.request_port_forward('127.0.0.1', PORT_REMOTE)
            
            print(f"[TUNNEL] Tunel activo: server.vitaminpos.cl -> VPS:{PORT_REMOTE} -> Local:{PORT_LOCAL}", flush=True)
            
            while True:
                chan = transport.accept(1000)
                if chan is None:
                    # Verificar si la conexión sigue viva
                    if not transport.is_active():
                        break
                    continue
                # Iniciar hilo de reenvío para esta conexión
                thr = threading.Thread(target=reverse_forward_handler, args=(chan, 'localhost', PORT_LOCAL))
                thr.daemon = True
                thr.start()
                
        except Exception as e:
            print(f"[TUNNEL ERROR] Error en el tunel SSH: {e}", flush=True)
        finally:
            client.close()
            print("[RETRY] Reintentando conectar en 10 segundos...", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    # 1. Iniciar Flask en un hilo independiente
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Esperar a que Flask arranque
    time.sleep(2)
    
    # 2. Iniciar el túnel SSH inverso en el hilo principal
    ssh_tunnel_loop()
