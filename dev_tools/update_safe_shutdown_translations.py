import json
import os

# Define the new keys and their translations
new_translations = {
    "es": {
        "msg_external_process": "⚠️ Servidor no lanzado por Antigravity. Cierre seguro NO disponible.",
        "msg_console_fail": "❌ No se pudo adjuntar a la consola. Cierre seguro NO disponible.",
        "msg_safe_shutdown_ok": "✅ Cierre seguro completado.",
        "msg_restart_aborted": "❌ Reinicio cancelado: Cierre no seguro.",
        "msg_force_kill_ask": "El servidor no respondió a Ctrl+C. ¿Forzar cierre? (Riesgo de pérdida de datos)"
    },
    "en": {
        "msg_external_process": "⚠️ Server not launched by Antigravity. Safe shutdown unavailable.",
        "msg_console_fail": "❌ Could not attach to console. Safe shutdown unavailable.",
        "msg_safe_shutdown_ok": "✅ Safe shutdown completed.",
        "msg_restart_aborted": "❌ Restart cancelled: Unsafe shutdown.",
        "msg_force_kill_ask": "Server did not respond to Ctrl+C. Force close? (Data loss risk)"
    },
    "pt": {
        "msg_external_process": "⚠️ Servidor não iniciado pelo Antigravity. Encerramento seguro indisponível.",
        "msg_console_fail": "❌ Não foi possível anexar ao console. Encerramento seguro indisponível.",
        "msg_safe_shutdown_ok": "✅ Encerramento seguro concluído.",
        "msg_restart_aborted": "❌ Reinício cancelado: Encerramento inseguro.",
        "msg_force_kill_ask": "O servidor não respondeu ao Ctrl+C. Forçar encerramento? (Risco de perda de dados)"
    },
    "fr": {
        "msg_external_process": "⚠️ Serveur non lancé par Antigravity. Arrêt sécurisé indisponible.",
        "msg_console_fail": "❌ Impossible de s'attacher à la console. Arrêt sécurisé indisponible.",
        "msg_safe_shutdown_ok": "✅ Arrêt sécurisé terminé.",
        "msg_restart_aborted": "❌ Redémarrage annulé : Arrêt non sécurisé.",
        "msg_force_kill_ask": "Le serveur n'a pas répondu à Ctrl+C. Forcer l'arrêt ? (Risque de perte de données)"
    },
    "ru": {
        "msg_external_process": "⚠️ Сервер не запущен Antigravity. Безопасное выключение недоступно.",
        "msg_console_fail": "❌ Не удалось подключиться к консоли. Безопасное выключение недоступно.",
        "msg_safe_shutdown_ok": "✅ Безопасное выключение завершено.",
        "msg_restart_aborted": "❌ Перезапуск отменен: Небезопасное выключение.",
        "msg_force_kill_ask": "Сервер не ответил на Ctrl+C. Принудительно закрыть? (Риск потери данных)"
    },
    "de": {
        "msg_external_process": "⚠️ Server nicht von Antigravity gestartet. Sicheres Herunterfahren nicht verfügbar.",
        "msg_console_fail": "❌ Konnte nicht an Konsole anhängen. Sicheres Herunterfahren nicht verfügbar.",
        "msg_safe_shutdown_ok": "✅ Sicheres Herunterfahren abgeschlossen.",
        "msg_restart_aborted": "❌ Neustart abgebrochen: Unsicheres Herunterfahren.",
        "msg_force_kill_ask": "Server antwortete nicht auf Ctrl+C. Schließen erzwingen? (Datenverlustrisiko)"
    },
    "zh": {
        "msg_external_process": "⚠️ 服务器非 Antigravity 启动。无法安全关闭。",
        "msg_console_fail": "❌ 无法附加到控制台。无法安全关闭。",
        "msg_safe_shutdown_ok": "✅ 安全关闭完成。",
        "msg_restart_aborted": "❌ 重启取消：关闭不安全。",
        "msg_force_kill_ask": "服务器未响应 Ctrl+C。强制关闭？（数据丢失风险）"
    },
    "hi": {
        "msg_external_process": "⚠️ सर्वर Antigravity द्वारा शुरू नहीं किया गया। सुरक्षित शटडाउन अनुपलब्ध।",
        "msg_console_fail": "❌ कंसोल से जुड़ नहीं सका। सुरक्षित शटडाउन अनुपलब्ध।",
        "msg_safe_shutdown_ok": "✅ सुरक्षित शटडाउन पूरा हुआ।",
        "msg_restart_aborted": "❌ पुनरारंभ रद्द: असुरक्षित शटडाउन।",
        "msg_force_kill_ask": "सर्वर ने Ctrl+C का उत्तर नहीं दिया। क्या जबरदस्ती बंद करें? (डेटा हानि का जोखिम)"
    },
    "ja": {
        "msg_external_process": "⚠️ サーバーはAntigravityによって起動されていません。安全なシャットダウンは利用できません。",
        "msg_console_fail": "❌ コンソールに接続できませんでした。安全なシャットダウンは利用できません。",
        "msg_safe_shutdown_ok": "✅ 安全なシャットダウンが完了しました。",
        "msg_restart_aborted": "❌ 再起動キャンセル：安全でないシャットダウン。",
        "msg_force_kill_ask": "サーバーがCtrl+Cに応答しませんでした。強制終了しますか？（データ損失のリスク）"
    }
}

lang_dir = os.path.join("data", "lang")

def update_lang_files():
    print(f"Updating files in {lang_dir}...")
    
    for filename in os.listdir(lang_dir):
        if not filename.endswith(".json"):
            continue
            
        lang_code = filename.split(".")[0]
        filepath = os.path.join(lang_dir, filename)
        
        if lang_code in new_translations:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update with new keys
                data.update(new_translations[lang_code])
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    
                print(f"Updated {filename}")
            except Exception as e:
                print(f"Error updating {filename}: {e}")
        else:
            print(f"Skipping {filename} (no translations defined)")

if __name__ == "__main__":
    update_lang_files()
