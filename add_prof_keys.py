import json, os, glob

# Keys nuevas para el panel de Perfiles
NEW_KEYS = {
    "es": {
        "prof_title":        "Perfiles de Configuración",
        "prof_create_hdr":   "✏  Crear / Editar Perfil",
        "prof_name_lbl_ui":  "Nombre:",
        "prof_add_setting":  "Agregar ajuste al perfil:",
        "prof_settings_list":"Ajustes del perfil:",
        "prof_clear_btn":    "Limpiar",
        "prof_apply_btn":    "▶  Aplicar Ahora",
        "prof_edit_btn":     "✏  Editar",
        "prof_my_profiles":  "📂  Mis Perfiles",
        "prof_save_full":    "💾  Guardar Perfil",
    },
    "en": {
        "prof_title":        "Configuration Profiles",
        "prof_create_hdr":   "✏  Create / Edit Profile",
        "prof_name_lbl_ui":  "Name:",
        "prof_add_setting":  "Add setting to profile:",
        "prof_settings_list":"Profile settings:",
        "prof_clear_btn":    "Clear",
        "prof_apply_btn":    "▶  Apply Now",
        "prof_edit_btn":     "✏  Edit",
        "prof_my_profiles":  "📂  My Profiles",
        "prof_save_full":    "💾  Save Profile",
    },
    "pt": {
        "prof_title":        "Perfis de Configuração",
        "prof_create_hdr":   "✏  Criar / Editar Perfil",
        "prof_name_lbl_ui":  "Nome:",
        "prof_add_setting":  "Adicionar ajuste ao perfil:",
        "prof_settings_list":"Ajustes do perfil:",
        "prof_clear_btn":    "Limpar",
        "prof_apply_btn":    "▶  Aplicar Agora",
        "prof_edit_btn":     "✏  Editar",
        "prof_my_profiles":  "📂  Meus Perfis",
        "prof_save_full":    "💾  Salvar Perfil",
    },
    "de": {
        "prof_title":        "Konfigurationsprofile",
        "prof_create_hdr":   "✏  Profil erstellen / bearbeiten",
        "prof_name_lbl_ui":  "Name:",
        "prof_add_setting":  "Einstellung hinzufügen:",
        "prof_settings_list":"Profileinstellungen:",
        "prof_clear_btn":    "Leeren",
        "prof_apply_btn":    "▶  Jetzt anwenden",
        "prof_edit_btn":     "✏  Bearbeiten",
        "prof_my_profiles":  "📂  Meine Profile",
        "prof_save_full":    "💾  Profil speichern",
    },
    "fr": {
        "prof_title":        "Profils de configuration",
        "prof_create_hdr":   "✏  Créer / Modifier profil",
        "prof_name_lbl_ui":  "Nom:",
        "prof_add_setting":  "Ajouter un paramètre:",
        "prof_settings_list":"Paramètres du profil:",
        "prof_clear_btn":    "Effacer",
        "prof_apply_btn":    "▶  Appliquer maintenant",
        "prof_edit_btn":     "✏  Modifier",
        "prof_my_profiles":  "📂  Mes profils",
        "prof_save_full":    "💾  Enregistrer profil",
    },
    "ru": {
        "prof_title":        "Профили конфигурации",
        "prof_create_hdr":   "✏  Создать / Изменить профиль",
        "prof_name_lbl_ui":  "Имя:",
        "prof_add_setting":  "Добавить настройку:",
        "prof_settings_list":"Настройки профиля:",
        "prof_clear_btn":    "Очистить",
        "prof_apply_btn":    "▶  Применить сейчас",
        "prof_edit_btn":     "✏  Изменить",
        "prof_my_profiles":  "📂  Мои профили",
        "prof_save_full":    "💾  Сохранить профиль",
    },
    "zh": {
        "prof_title":        "配置文件",
        "prof_create_hdr":   "✏  创建 / 编辑配置",
        "prof_name_lbl_ui":  "名称:",
        "prof_add_setting":  "添加设置:",
        "prof_settings_list":"配置设置:",
        "prof_clear_btn":    "清除",
        "prof_apply_btn":    "▶  立即应用",
        "prof_edit_btn":     "✏  编辑",
        "prof_my_profiles":  "📂  我的配置",
        "prof_save_full":    "💾  保存配置",
    },
    "ja": {
        "prof_title":        "設定プロファイル",
        "prof_create_hdr":   "✏  プロファイルの作成/編集",
        "prof_name_lbl_ui":  "名前:",
        "prof_add_setting":  "設定を追加:",
        "prof_settings_list":"プロファイル設定:",
        "prof_clear_btn":    "クリア",
        "prof_apply_btn":    "▶  今すぐ適用",
        "prof_edit_btn":     "✏  編集",
        "prof_my_profiles":  "📂  マイプロファイル",
        "prof_save_full":    "💾  プロファイル保存",
    },
    "hi": {
        "prof_title":        "कॉन्फ़िगरेशन प्रोफ़ाइल",
        "prof_create_hdr":   "✏  प्रोफ़ाइल बनाएं / संपादित करें",
        "prof_name_lbl_ui":  "नाम:",
        "prof_add_setting":  "सेटिंग जोड़ें:",
        "prof_settings_list":"प्रोफ़ाइल सेटिंग:",
        "prof_clear_btn":    "साफ़ करें",
        "prof_apply_btn":    "▶  अभी लागू करें",
        "prof_edit_btn":     "✏  संपादित करें",
        "prof_my_profiles":  "📂  मेरी प्रोफ़ाइल",
        "prof_save_full":    "💾  प्रोफ़ाइल सहेजें",
    },
}

lang_dir = os.path.join(os.path.dirname(__file__), "data", "lang")

for lang_code, new_keys in NEW_KEYS.items():
    path = os.path.join(lang_dir, f"{lang_code}.json")
    if not os.path.exists(path):
        print(f"SKIP (not found): {path}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    added = 0
    for k, v in new_keys.items():
        if k not in data:
            data[k] = v
            added += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[{lang_code}] +{added} keys added")

print("Done.")
