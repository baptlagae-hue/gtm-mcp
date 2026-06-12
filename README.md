# Google Tag Manager (GTM) Local MCP Server

Ce dépôt contient un serveur MCP (Model Context Protocol) local pour Google Tag Manager (GTM). Il permet à n'importe quel agent d'IA (Claude Code, Cursor, Claude Desktop, Gemini, etc.) d'interagir en toute sécurité avec vos comptes GTM.

Le serveur est **model-agnostic** par design : il utilise le protocole standardisé MCP d'Anthropic sur l'entrée/sortie standard (stdio) pour exposer ses outils de manière sécurisée.

---

## 🛡️ Règles de Gouvernance et de Sécurité

Pour éviter tout incident sur vos conteneurs GTM de production, le serveur applique des garde-fous stricts directement dans le code :

1. **Pas de Publication ni de Suppression** : Le serveur ne dispose d'aucun outil (tool) pour publier des conteneurs, créer des versions ou supprimer des éléments.
2. **Nomenclature Obligatoire** : Les nouveaux workspaces doivent impérativement commencer par le préfixe **`MS | `** (permettant de distinguer les workspaces gérés par l'IA des workspaces créés manuellement ou par défaut).
3. **Protection des Espaces de Travail Existants** : Toute création de balise, déclencheur ou variable dans un espace de travail qui ne commence pas par `MS | ` (comme le `Default Workspace` ou vos workspaces manuels) est automatiquement bloquée.
4. **Pas de Secrets dans le Code** : Le serveur utilise les Application Default Credentials (ADC) de Google Cloud. **Ne committez jamais de fichier `client_secrets.json` ou de clés privées sur GitHub.**

---

## ⚙️ Prérequis et Authentification

### 1. Installer le SDK Google Cloud (`gcloud`)
Le serveur utilise votre session utilisateur locale pour appeler l'API GTM. Vous devez avoir le SDK Google Cloud installé sur votre machine.

### 2. Se connecter localement (Application Default Credentials)
Exécutez la commande suivante dans votre terminal pour autoriser l'accès à GTM :
```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/tagmanager.edit.containers,https://www.googleapis.com/auth/cloud-platform
```
Cette commande ouvrira votre navigateur pour vous authentifier avec votre compte Google disposant des droits sur GTM.

---

## 🚀 Installation Locale

1. Clonez ce dépôt sur votre machine :
   ```bash
   git clone <url-de-votre-repo-github>
   cd gtm-mcp
   ```

2. Créez un environnement virtuel et installez les dépendances :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. (Optionnel) Installez le package en mode éditable pour pouvoir utiliser la commande globale `gtm-mcp` :
   ```bash
   pip install -e .
   ```

---

## 🤖 Configuration avec Claude Code

**Claude Code** supporte nativement le protocole MCP. Vous pouvez ajouter le serveur GTM MCP de deux manières :

### Option A : Via la ligne de commande Claude Code (Recommandé)
Pour ajouter le serveur dans votre configuration globale d'utilisateur, exécutez la commande suivante depuis votre terminal :

```bash
claude mcp add gtm-mcp -- python3 /chemin/vers/gtm-mcp/gtm_mcp/server.py
```
*(Remplacez `/chemin/vers/gtm-mcp` par le chemin absolu où vous avez cloné le dépôt)*

Vous pouvez lister les serveurs actifs pour vérifier la connexion :
```bash
claude mcp list
```

### Option B : Via modification manuelle du fichier de configuration
Vous pouvez directement éditer le fichier de configuration de Claude Code.

* **Portée Utilisateur (tous les projets) :** Éditez ou créez le fichier `~/.claude.json` :
  ```json
  {
    "mcpServers": {
      "gtm-mcp": {
        "command": "python3",
        "args": ["/chemin/vers/gtm-mcp/gtm_mcp/server.py"]
      }
    }
  }
  ```

* **Portée Projet (partagé avec l'équipe) :** Créez un fichier `.mcp.json` à la racine de votre projet de développement :
  ```json
  {
    "mcpServers": {
      "gtm-mcp": {
        "command": "python3",
        "args": ["/chemin/vers/gtm-mcp/gtm_mcp/server.py"]
      }
    }
  }
  ```

---

## 💻 Configuration avec Claude Desktop

Pour utiliser ce serveur dans l'application de bureau Claude Desktop, ajoutez cette configuration dans votre fichier `~/Library/Application Support/Claude/claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "gtm-mcp": {
      "command": "python3",
      "args": [
        "/chemin/vers/gtm-mcp/gtm_mcp/server.py"
      ]
    }
  }
}
```

---

## 🛠️ Déploiement sur GitHub

Pour héberger ce projet sur votre compte personnel GitHub :

1. Initialisez le dépôt Git local :
   ```bash
   git init
   git add .
   git commit -m "Initial commit: GTM MCP Server with governance guardrails"
   ```

2. Créez un nouveau dépôt vide sur GitHub (ex: `gtm-mcp`), puis associez le dépôt local et poussez le code :
   ```bash
   git branch -M main
   git remote add origin https://github.com/<votre-utilisateur>/gtm-mcp.git
   git push -u origin main
   ```

*(Le fichier `.gitignore` configuré à la racine bloquera automatiquement tout fichier `client_secrets.json` ou `.env` accidentel afin de sécuriser vos identifiants).*
