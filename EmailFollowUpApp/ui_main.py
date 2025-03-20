"""
Main UI for EmailFollowUpApp
Implements the main window and user interface components
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QTextEdit, QComboBox,
    QSystemTrayIcon, QMenu, QAction, QTabWidget, QProgressBar,
    QDateTimeEdit, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QDateTime
from PyQt5.QtGui import QIcon, QFont
from datetime import datetime
import json

from log_manager import get_logger
from email_manager import get_email_manager
from scheduler import get_scheduler
from config import EMAIL_SERVERS, DEFAULT_FOLLOWUP_TEMPLATE
from utils import validate_email, format_date

logger = get_logger()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Email Settings Group
        email_group = QGroupBox("Configuration Email")
        email_layout = QFormLayout()
        
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.server_type = QComboBox()
        for server in EMAIL_SERVERS.keys():
            self.server_type.addItem(server.capitalize())
        
        email_layout.addRow("Adresse Email:", self.email_input)
        email_layout.addRow("Mot de passe:", self.password_input)
        email_layout.addRow("Type de serveur:", self.server_type)
        email_group.setLayout(email_layout)
        
        # Followup Settings Group
        followup_group = QGroupBox("Configuration des relances")
        followup_layout = QFormLayout()
        
        self.check_interval = QSpinBox()
        self.check_interval.setRange(1, 1440)  # 1 minute to 24 hours
        self.check_interval.setValue(30)  # Default 30 minutes
        self.check_interval.setSuffix(" minutes")
        
        self.auto_start = QCheckBox()
        self.minimize_to_tray = QCheckBox()
        
        followup_layout.addRow("Intervalle de vérification:", self.check_interval)
        followup_layout.addRow("Démarrage automatique:", self.auto_start)
        followup_layout.addRow("Minimiser dans la barre des tâches:", self.minimize_to_tray)
        followup_group.setLayout(followup_layout)
        
        # Template Settings Group
        template_group = QGroupBox("Modèle de relance")
        template_layout = QVBoxLayout()
        
        self.template_edit = QTextEdit()
        self.template_edit.setPlainText(DEFAULT_FOLLOWUP_TEMPLATE)
        template_layout.addWidget(self.template_edit)
        template_group.setLayout(template_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Enregistrer")
        cancel_button = QPushButton("Annuler")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Add all components to main layout
        layout.addWidget(email_group)
        layout.addWidget(followup_group)
        layout.addWidget(template_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class AddFollowupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un suivi")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()
        
        # Email details
        self.recipient_input = QLineEdit()
        self.subject_input = QLineEdit()
        
        # Dates
        self.sent_date = QDateTimeEdit(QDateTime.currentDateTime())
        self.delay_days = QSpinBox()
        self.delay_days.setRange(1, 365)
        self.delay_days.setValue(7)
        self.delay_days.setSuffix(" jours")
        
        # Add fields to layout
        layout.addRow("Destinataire:", self.recipient_input)
        layout.addRow("Sujet:", self.subject_input)
        layout.addRow("Date d'envoi:", self.sent_date)
        layout.addRow("Délai de relance:", self.delay_days)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Ajouter")
        cancel_button = QPushButton("Annuler")
        
        add_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)
        
        # Add button layout to main layout
        layout.addRow("", button_layout)
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.email_manager = get_email_manager()
        self.scheduler = get_scheduler()
        self.setup_ui()
        self.setup_tray()
        self.setup_connections()

    def setup_ui(self):
        self.setWindowTitle("EmailFollowUpApp")
        self.setMinimumSize(800, 600)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Followups tab
        followups_tab = QWidget()
        followups_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.add_button = QPushButton("Ajouter un suivi")
        self.add_button.clicked.connect(self.show_add_dialog)
        
        self.refresh_button = QPushButton("Actualiser")
        self.refresh_button.clicked.connect(self.refresh_followups)
        
        self.settings_button = QPushButton("Paramètres")
        self.settings_button.clicked.connect(self.show_settings)
        
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.refresh_button)
        toolbar.addWidget(self.settings_button)
        toolbar.addStretch()
        
        # Status indicator
        self.status_label = QLabel("État: Inactif")
        toolbar.addWidget(self.status_label)
        
        followups_layout.addLayout(toolbar)
        
        # Followups table
        self.followups_table = QTableWidget()
        self.followups_table.setColumnCount(7)
        self.followups_table.setHorizontalHeaderLabels([
            "ID", "Destinataire", "Sujet", "Date d'envoi",
            "Date de relance", "Statut", "Actions"
        ])
        self.followups_table.horizontalHeader().setStretchLastSection(True)
        
        followups_layout.addWidget(self.followups_table)
        followups_tab.setLayout(followups_layout)
        
        # Logs tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        logs_layout.addWidget(self.log_text)
        logs_tab.setLayout(logs_layout)
        
        # Add tabs
        tabs.addTab(followups_tab, "Suivis")
        tabs.addTab(logs_tab, "Logs")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Prêt")
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)

    def setup_tray(self):
        """Set up system tray icon and menu"""
        # Créer l'icône de la barre des tâches
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        self.tray_icon.setToolTip("EmailFollowUpApp - Suivi des emails")
        
        # Connecter le double-clic sur l'icône
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Créer le menu contextuel
        tray_menu = QMenu()
        
        # Action pour afficher/cacher la fenêtre
        self.show_action = QAction("Afficher", self)
        self.show_action.triggered.connect(self.show_hide_window)
        
        # Actions pour le contrôle de l'application
        start_scheduler_action = QAction("Démarrer le suivi", self)
        start_scheduler_action.triggered.connect(self.scheduler.start)
        
        stop_scheduler_action = QAction("Arrêter le suivi", self)
        stop_scheduler_action.triggered.connect(self.scheduler.stop)
        
        force_check_action = QAction("Vérifier maintenant", self)
        force_check_action.triggered.connect(self.scheduler.force_check)
        
        settings_action = QAction("Paramètres", self)
        settings_action.triggered.connect(self.show_settings)
        
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close_application)
        
        # Ajouter les actions au menu
        tray_menu.addAction(self.show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(start_scheduler_action)
        tray_menu.addAction(stop_scheduler_action)
        tray_menu.addAction(force_check_action)
        tray_menu.addSeparator()
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        # Définir le menu contextuel
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_hide_window(self):
        """Afficher ou cacher la fenêtre principale"""
        if self.isVisible():
            self.hide()
            self.show_action.setText("Afficher")
        else:
            self.show()
            self.show_action.setText("Réduire")
            self.activateWindow()

    def on_tray_icon_activated(self, reason):
        """Gérer l'activation de l'icône de la barre des tâches"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_hide_window()
        elif reason == QSystemTrayIcon.Trigger:
            # Clic simple : afficher un message avec le statut
            status = "actif" if self.scheduler.is_active() else "inactif"
            self.show_tray_message(
                "État du suivi",
                f"Le suivi des emails est {status}",
                QSystemTrayIcon.Information
            )

    def show_tray_message(self, title: str, message: str, icon=QSystemTrayIcon.Information):
        """Afficher une notification dans la barre des tâches"""
        self.tray_icon.showMessage(title, message, icon, 3000)

    def setup_connections(self):
        """Set up signal connections"""
        # Connect scheduler signals
        self.scheduler.check_started.connect(self.on_check_started)
        self.scheduler.check_completed.connect(self.on_check_completed)
        self.scheduler.followup_sent.connect(self.on_followup_sent)
        self.scheduler.response_detected.connect(self.on_response_detected)
        self.scheduler.error_occurred.connect(self.on_error)

    def show_add_dialog(self):
        """Show dialog to add new followup"""
        dialog = AddFollowupDialog(self)
        if dialog.exec_():
            try:
                # Validate input
                recipient = dialog.recipient_input.text()
                if not validate_email(recipient):
                    raise ValueError("Adresse email invalide")
                
                # Prepare followup data
                followup_data = {
                    'recipient': recipient,
                    'subject': dialog.subject_input.text(),
                    'sent_date': dialog.sent_date.dateTime().toPyDateTime(),
                    'delay_days': dialog.delay_days.value(),
                    'sender': self.email_manager.smtp.username
                }
                
                # Add followup
                followup_id = self.email_manager.add_followup(followup_data)
                if followup_id:
                    self.refresh_followups()
                    self.statusBar().showMessage("Suivi ajouté avec succès", 3000)
                else:
                    raise Exception("Échec de l'ajout du suivi")
                    
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            try:
                # Save email settings
                username = dialog.email_input.text()
                password = dialog.password_input.text()
                server_type = dialog.server_type.currentText().lower()
                
                if username and password:
                    if self.email_manager.connect(username, password, server_type):
                        self.statusBar().showMessage("Connexion réussie", 3000)
                    else:
                        raise Exception("Échec de la connexion")
                
                # Save other settings
                interval = dialog.check_interval.value() * 60  # Convert to seconds
                self.scheduler.set_check_interval(interval)
                
                # Start/stop scheduler based on auto_start
                if dialog.auto_start.isChecked():
                    self.scheduler.start()
                else:
                    self.scheduler.stop()
                
                self.refresh_followups()
                
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))

    def refresh_followups(self):
        """Refresh followups table"""
        try:
            followups = self.email_manager.db.get_all_followups()
            
            self.followups_table.setRowCount(len(followups))
            
            for row, followup in enumerate(followups):
                # Add followup data to table
                self.followups_table.setItem(row, 0, QTableWidgetItem(str(followup['id'])))
                self.followups_table.setItem(row, 1, QTableWidgetItem(followup['recipient']))
                self.followups_table.setItem(row, 2, QTableWidgetItem(followup['subject']))
                self.followups_table.setItem(row, 3, QTableWidgetItem(
                    format_date(followup['sent_date'])
                ))
                self.followups_table.setItem(row, 4, QTableWidgetItem(
                    format_date(followup['followup_date'])
                ))
                self.followups_table.setItem(row, 5, QTableWidgetItem(followup['status']))
                
                # Add action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                edit_button = QPushButton("Modifier")
                edit_button.clicked.connect(lambda _, fid=followup['id']: self.edit_followup(fid))
                
                delete_button = QPushButton("Supprimer")
                delete_button.clicked.connect(lambda _, fid=followup['id']: self.delete_followup(fid))
                
                actions_layout.addWidget(edit_button)
                actions_layout.addWidget(delete_button)
                
                self.followups_table.setCellWidget(row, 6, actions_widget)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du rafraîchissement : {str(e)}")

    def edit_followup(self, followup_id: int):
        """Edit existing followup"""
        try:
            followup = self.email_manager.db.get_followup_by_email_id(followup_id)
            if not followup:
                raise Exception("Suivi non trouvé")
            
            dialog = AddFollowupDialog(self)
            
            # Pre-fill dialog with existing data
            dialog.recipient_input.setText(followup['recipient'])
            dialog.subject_input.setText(followup['subject'])
            dialog.sent_date.setDateTime(followup['sent_date'])
            dialog.delay_days.setValue(followup['delay_days'])
            
            if dialog.exec_():
                # Update followup
                updated_data = {
                    'recipient': dialog.recipient_input.text(),
                    'subject': dialog.subject_input.text(),
                    'sent_date': dialog.sent_date.dateTime().toPyDateTime(),
                    'delay_days': dialog.delay_days.value()
                }
                
                if self.email_manager.db.update_followup(followup_id, updated_data):
                    self.refresh_followups()
                    self.statusBar().showMessage("Suivi mis à jour avec succès", 3000)
                else:
                    raise Exception("Échec de la mise à jour")
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def delete_followup(self, followup_id: int):
        """Delete followup"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "Voulez-vous vraiment supprimer ce suivi ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.email_manager.db.delete_followup(followup_id):
                    self.refresh_followups()
                    self.statusBar().showMessage("Suivi supprimé avec succès", 3000)
                else:
                    raise Exception("Échec de la suppression")
                    
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    @pyqtSlot()
    def on_check_started(self):
        """Handle check started signal"""
        self.status_label.setText("État: Vérification en cours...")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        
        # Notification dans la barre des tâches
        self.show_tray_message(
            "Vérification en cours",
            "Recherche de nouvelles réponses...",
            QSystemTrayIcon.Information
        )

    @pyqtSlot(bool)
    def on_check_completed(self, success: bool):
        """Handle check completed signal"""
        self.progress_bar.hide()
        status = "État: Actif" if success else "État: Erreur lors de la vérification"
        self.status_label.setText(status)
        self.refresh_followups()
        
        if not success:
            # Notification d'erreur
            self.show_tray_message(
                "Erreur de vérification",
                "Une erreur est survenue lors de la vérification des emails",
                QSystemTrayIcon.Warning
            )

    @pyqtSlot(int)
    def on_followup_sent(self, followup_id: int):
        """Handle followup sent signal"""
        message = f"Relance envoyée pour le suivi #{followup_id}"
        self.statusBar().showMessage(message, 3000)
        self.refresh_followups()
        
        # Notification de relance envoyée
        self.show_tray_message(
            "Relance envoyée",
            message,
            QSystemTrayIcon.Information
        )

    @pyqtSlot(int)
    def on_response_detected(self, followup_id: int):
        """Handle response detected signal"""
        message = f"Réponse détectée pour le suivi #{followup_id}"
        self.statusBar().showMessage(message, 3000)
        self.refresh_followups()
        
        # Notification de réponse détectée
        self.show_tray_message(
            "Nouvelle réponse",
            message,
            QSystemTrayIcon.Information
        )

    @pyqtSlot(str)
    def on_error(self, error_msg: str):
        """Handle error signal"""
        self.status_label.setText("État: Erreur")
        QMessageBox.warning(self, "Erreur", error_msg)
        
        # Notification d'erreur
        self.show_tray_message(
            "Erreur",
            error_msg,
            QSystemTrayIcon.Critical
        )

    def closeEvent(self, event):
        """Handle application close event"""
        if self.tray_icon.isVisible():
            QMessageBox.information(
                self,
                "EmailFollowUpApp",
                "L'application continuera à s'exécuter en arrière-plan. "
                "Pour la quitter complètement, utilisez le menu de la barre des tâches."
            )
            self.hide()
            event.ignore()
        else:
            self.close_application()

    def close_application(self):
        """Close the application properly"""
        try:
            # Stop scheduler
            self.scheduler.stop()
            
            # Disconnect from email servers
            self.email_manager.disconnect()
            
            # Close database connection
            self.email_manager.db.close()
            
            QApplication.quit()
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            QApplication.quit()

def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()