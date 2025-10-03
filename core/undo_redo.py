# coding: utf-8
import os
import shutil
from .history import charger_historique, sauvegarder_historique
from logs.logger import logger

# Piles globales pour undo/redo
undo_stack = []
redo_stack = []

# Taille maximale pour limiter l'utilisation de la mémoire
MAX_HISTORY_SIZE = 50

def enregistrer_action(action_type, source, destination, metadata=None):
    """
    Enregistre une action dans l'historique et dans la pile undo
    """
    action = {
        "action": action_type,
        "source": source,
        "destination": destination,
        "metadata": metadata or {}
    }
    
    # Ajouter à la pile undo
    global undo_stack, redo_stack
    undo_stack.append(action)
    
    # Limiter la taille de la pile
    if len(undo_stack) > MAX_HISTORY_SIZE:
        undo_stack.pop(0)
    
    # Une nouvelle action vide la pile redo
    redo_stack.clear()
    
    # Aussi enregistrer dans le fichier d'historique
    historique = charger_historique()
    historique.append(action)
    # Limiter aussi la taille du fichier historique
    if len(historique) > MAX_HISTORY_SIZE * 2:  # on peut garder plus dans le fichier
        historique = historique[-MAX_HISTORY_SIZE * 2:]
    sauvegarder_historique(historique)
    
    logger.info(f"Action enregistrée: {action_type}, {source} → {destination}")

def undo():
    """
    Annule la dernière action effectuée
    """
    global undo_stack, redo_stack
    
    if not undo_stack:
        logger.warning("Aucune action à annuler.")
        return False
    
    # Récupérer la dernière action
    action = undo_stack.pop()
    action_type = action["action"]
    source = action["source"]
    destination = action["destination"]
    metadata = action.get("metadata", {})
    
    success = False
    
    # Traiter selon le type d'action
    if action_type == "Déplacement":
        if os.path.exists(destination):
            try:
                # Créer le dossier parent s'il n'existe pas
                parent_dir = os.path.dirname(source)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                
                shutil.move(destination, source)
                logger.info(f"Action annulée: {action_type}, {destination} → {source}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors de l'annulation du déplacement: {e}")
        else:
            logger.error(f"Impossible d'annuler : {destination} introuvable.")
    
    elif action_type == "Copie":
        # Pour une copie, on supprime simplement la destination
        if os.path.exists(destination):
            try:
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
                logger.info(f"Action annulée: {action_type}, suppression de {destination}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors de l'annulation de la copie: {e}")
        else:
            logger.error(f"Impossible d'annuler : {destination} introuvable.")
    
    elif action_type == "Suppression":
        # Pour une suppression, on restaure à partir de la corbeille ou des métadonnées
        corbeille_path = metadata.get("corbeille_path")
        contenu = metadata.get("contenu")
        
        try:
            if corbeille_path and os.path.exists(corbeille_path):
                # Créer le dossier parent s'il n'existe pas
                parent_dir = os.path.dirname(source)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                    
                shutil.move(corbeille_path, source)
                logger.info(f"Action annulée: {action_type}, restauration de {source}")
                success = True
            elif contenu is not None:
                # Si on a sauvegardé le contenu pour les petits fichiers
                parent_dir = os.path.dirname(source)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                    
                with open(source, 'wb') as f:
                    f.write(contenu)
                logger.info(f"Action annulée: {action_type}, recréation de {source}")
                success = True
            else:
                logger.error(f"Impossible de restaurer {source}, données non disponibles.")
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {e}")
    
    elif action_type == "Renommage":
        # Le renommage est similaire au déplacement
        if os.path.exists(destination):
            try:
                shutil.move(destination, source)
                logger.info(f"Action annulée: {action_type}, {destination} → {source}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors de l'annulation du renommage: {e}")
        else:
            logger.error(f"Impossible d'annuler : {destination} introuvable.")
    
    elif action_type == "Création":
        # Pour la création, on supprime simplement l'élément créé
        if os.path.exists(destination):
            try:
                if os.path.isdir(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
                logger.info(f"Action annulée: {action_type}, suppression de {destination}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors de l'annulation de la création: {e}")
        else:
            logger.error(f"Impossible d'annuler : {destination} introuvable.")
    
    # Si l'action a été annulée avec succès, l'ajouter à la pile redo
    if success:
        # Pour le redo, on inverse source et destination
        inverse_action = action.copy()
        # Pas besoin d'inverser pour tous les types d'actions
        redo_stack.append(inverse_action)
        
        # Mettre à jour le fichier d'historique
        historique = charger_historique()
        if historique and historique[-1] == action:
            historique.pop()
            sauvegarder_historique(historique)
        
        return True
    
    return False

def redo():
    """
    Rétablit la dernière action annulée
    """
    global undo_stack, redo_stack
    
    if not redo_stack:
        logger.warning("Aucune action à rétablir.")
        return False
    
    # Récupérer la dernière action annulée
    action = redo_stack.pop()
    action_type = action["action"]
    source = action["source"]
    destination = action["destination"]
    metadata = action.get("metadata", {})
    
    success = False
    
    # Traiter selon le type d'action
    if action_type == "Déplacement":
        if os.path.exists(source):
            try:
                # Créer le dossier parent s'il n'existe pas
                parent_dir = os.path.dirname(destination)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                
                shutil.move(source, destination)
                logger.info(f"Action refaite: {action_type}, {source} → {destination}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors du rétablissement du déplacement: {e}")
        else:
            logger.error(f"Impossible de rétablir : {source} introuvable.")
    
    elif action_type == "Copie":
        if os.path.exists(source):
            try:
                # Créer le dossier parent s'il n'existe pas
                parent_dir = os.path.dirname(destination)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                
                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
                logger.info(f"Action refaite: {action_type}, {source} → {destination}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors du rétablissement de la copie: {e}")
        else:
            logger.error(f"Impossible de rétablir : {source} introuvable.")
    
    elif action_type == "Suppression":
        if os.path.exists(source):
            try:
                # Si une corbeille est définie, déplacer vers la corbeille
                corbeille_path = metadata.get("corbeille_path")
                if corbeille_path:
                    parent_dir = os.path.dirname(corbeille_path)
                    if not os.path.exists(parent_dir):
                        os.makedirs(parent_dir)
                    shutil.move(source, corbeille_path)
                else:
                    # Sinon suppression directe
                    if os.path.isdir(source):
                        shutil.rmtree(source)
                    else:
                        os.remove(source)
                logger.info(f"Action refaite: {action_type}, suppression de {source}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors du rétablissement de la suppression: {e}")
        else:
            logger.error(f"Impossible de rétablir : {source} introuvable.")
    
    elif action_type == "Renommage":
        if os.path.exists(source):
            try:
                # Créer le dossier parent s'il n'existe pas
                parent_dir = os.path.dirname(destination)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                
                shutil.move(source, destination)
                logger.info(f"Action refaite: {action_type}, {source} → {destination}")
                success = True
            except Exception as e:
                logger.error(f"Erreur lors du rétablissement du renommage: {e}")
        else:
            logger.error(f"Impossible de rétablir : {source} introuvable.")
    
    elif action_type == "Création":
        # Recréer l'élément à partir des métadonnées
        try:
            est_dossier = metadata.get("est_dossier", False)
            contenu = metadata.get("contenu")
            
            parent_dir = os.path.dirname(destination)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            if est_dossier:
                if not os.path.exists(destination):
                    os.makedirs(destination)
            elif contenu is not None:
                with open(destination, 'wb') as f:
                    f.write(contenu)
            else:
                # Créer un fichier vide si aucun contenu
                with open(destination, 'w') as f:
                    pass
            
            logger.info(f"Action refaite: {action_type}, création de {destination}")
            success = True
        except Exception as e:
            logger.error(f"Erreur lors du rétablissement de la création: {e}")
    
    # Si l'action a été refaite avec succès, l'ajouter à la pile undo
    if success:
        undo_stack.append(action)
        
        # Mettre à jour le fichier d'historique
        historique = charger_historique()
        historique.append(action)
        sauvegarder_historique(historique)
        
        return True
    
    return False

def clear_history():
    """
    Vide l'historique des actions
    """
    global undo_stack, redo_stack
    undo_stack.clear()
    redo_stack.clear()
    sauvegarder_historique([])
    logger.info("Historique des actions effacé.")

def peut_annuler():
    """
    Vérifie s'il est possible d'annuler une action
    """
    return len(undo_stack) > 0

def peut_retablir():
    """
    Vérifie s'il est possible de rétablir une action
    """
    return len(redo_stack) > 0

# Fonctions utilitaires pour gérer les différents types d'actions

def enregistrer_deplacement(source, destination):
    enregistrer_action("Déplacement", source, destination)

def enregistrer_copie(source, destination):
    enregistrer_action("Copie", source, destination)

def enregistrer_suppression(source, destination="", corbeille_path=None):
    metadata = {"corbeille_path": corbeille_path}
    
    # Pour les petits fichiers, on peut aussi sauvegarder le contenu
    if os.path.isfile(source) and os.path.getsize(source) < 1024 * 1024:  # 1MB max
        try:
            with open(source, 'rb') as f:
                contenu = f.read()
            metadata["contenu"] = contenu
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder le contenu de {source}: {e}")
    
    enregistrer_action("Suppression", source, destination, metadata)

def enregistrer_renommage(ancien_nom, nouveau_nom):
    enregistrer_action("Renommage", ancien_nom, nouveau_nom)

def enregistrer_creation(chemin, est_dossier=False, contenu=None):
    metadata = {
        "est_dossier": est_dossier,
        "contenu": contenu
    }
    # Pour le undo d'une création, on utilise une destination fictive
    enregistrer_action("Création", "", chemin, metadata)