# EmailFollowUpApp

Application de suivi et de relance automatique des emails pour Mailbird.

## 🔹 Fonctionnalités

- Suivi automatique des emails envoyés
- Relances automatiques après X jours sans réponse
- Annulation automatique des relances si une réponse est détectée
- Interface utilisateur intuitive
- Intégration avec les serveurs email via IMAP/SMTP
- Détection intelligente des réponses (ignore les réponses automatiques)
- Modèles de relance personnalisables
- Journalisation des actions et des erreurs

## 🔹 Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-username/EmailFollowUpApp.git
cd EmailFollowUpApp
```

2. Créer un environnement virtuel Python :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🔹 Configuration

1. Lancer l'application :
```bash
python main.py
```

2. Dans l'interface, cliquer sur "Paramètres" pour configurer :
   - Vos identifiants email (Gmail, Outlook, etc.)
   - L'intervalle de vérification des réponses
   - Les modèles de relance
   - Les options de démarrage automatique

## 🔹 Utilisation

### Ajouter un suivi d'email

1. Cliquer sur "Ajouter un suivi"
2. Remplir les informations :
   - Destinataire
   - Sujet
   - Date d'envoi
   - Délai de relance (en jours)
3. Valider

### Gérer les suivis

- Le tableau principal affiche tous les suivis en cours
- Pour chaque suivi, vous pouvez :
  - Voir son statut
  - Modifier les paramètres
  - Annuler le suivi
  - Voir l'historique des relances

### Paramètres avancés

- Configuration des serveurs email
- Personnalisation des modèles de relance
- Gestion des réponses automatiques à ignorer
- Options de notification

## 🔹 Structure du projet

```
EmailFollowUpApp/
├── main.py              # Point d'entrée de l'application
├── config.py            # Configuration globale
├── utils.py            # Fonctions utilitaires
├── database.py         # Gestion de la base de données
├── email_manager.py    # Gestion des emails
├── imap_client.py      # Client IMAP
├── smtp_client.py      # Client SMTP
├── scheduler.py        # Planificateur de tâches
├── ui_main.py          # Interface utilisateur
├── log_manager.py      # Gestion des logs
├── requirements.txt    # Dépendances Python
└── logs/              # Dossier des fichiers de log
```

## 🔹 Dépendances principales

- Python 3.7+
- PyQt5 : Interface graphique
- python-dateutil : Manipulation des dates

## 🔹 Fonctionnement en arrière-plan

L'application peut être minimisée dans la barre des tâches et continuera à :
- Vérifier les réponses aux emails suivis
- Envoyer les relances automatiques
- Journaliser les actions

## 🔹 Sécurité

- Les mots de passe sont stockés de manière sécurisée
- Les connexions IMAP/SMTP utilisent SSL/TLS
- Aucune donnée n'est envoyée à des serveurs externes

## 🔹 Support

Pour toute question ou problème :
1. Consulter les logs dans le dossier `logs/`
2. Vérifier les paramètres de connexion email
3. S'assurer que l'accès IMAP/SMTP est activé sur votre compte email

## 🔹 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.