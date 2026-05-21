# ⚡ Shemas / PCB

Ce dépôt contient l'ensemble des fichiers de conception matérielle (Hardware) de la carte électronique réalisée dans le cadre de ce projet.

## 📋 Description du Projet
<!-- Décris ici brièvement à quoi sert ta carte (ex: acquisition de données de température, contrôle de modules, interface de communication...) -->
Ce projet consiste en la conception, la saisie du schéma et le routage d'un circuit imprimé (PCB) répondant aux exigences du cahier des charges.

## 🛠️ Spécifications Techniques
*   **Logiciel de CAO :** KiCad 9.0
*   **Règles de conception (Design Rules) :**
    *   Largeur des pistes par défaut : 20th (0.508 mm)
*   **Nombre de couches :** 1 couches (Bottom)
*   **Composants principaux :**
   - Lilygo T-A7670
   - Adafruit Max31875
   - PT100

## 📁 Structure du Projet
*   `*.kicad_pro` : Fichier principal du projet KiCad.
*   `*.kicad_sch` : Fichier du schéma électrique.
*   `*.kicad_pcb` : Fichier de routage du circuit imprimé.
*   `/gerber/` : (Optionnel) Fichiers d'exportation pour la fabrication de la carte.

## 🚀 Comment ouvrir le projet
1. Assurez-vous d'avoir installé **KiCad (version 9.0 ou supérieure)**.
2. Clonez ce dépôt ou téléchargez les fichiers.
3. Lancez KiCad et ouvrez le fichier `.kicad_pro` situé à la racine.

## 👤 Auteur
**Robin Paniagua Desclaux**
*Étudiant en BTS CIEL ER (1ère année)*
