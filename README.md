# Ubisoft Scraper & Dashboard

Ce projet a pour objectif de collecter, stocker et visualiser les données des jeux du catalogue Ubisoft Store France. Tout ceci sera affiché via une application interactive. 
Il s'appuie sur une architectre de conteneurs pour garantir la portabilité et la modularité des services.

## Fonctionnalités clés


## Choix techniques
## Architecture globale
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span>Project
|-- scraper
│   │-- Dockerfile
│   │-- main.py             # Script de scraping, nettoyage et injection Mongo
│   │-- requirements.txt
│-- app
│   │-- Dockerfile
│   │-- main.py             # Application Streamlit
│   │-- requirements.txt
|-- docker-compose.yml      # Orchestration des services
|-- README.md               # Documentation générale
</pre></div>

  
## Installation 

Pour pouvoir lancer le scraping et l'application : 

1 - Assurez vous d'avoir installé et configuré Docker. 

2 - Cloner le projet dans votre environnement local : 

<div class="highlight"><pre><span></span>$ git clone https://github.com/<Nom-du-repo>/Data-Engineering-Project.git
</pre></div>

3 - Lancer l'environnement : 

<div class="highlight"><pre><span></span>$ docker-compose up --build
</pre></div>

Cette commande lancera automatiquement la base de données MongoDB, exécute le scraper et démarre l'interface Streamlit. 

4 - Accédez au dashboard sur un navigateur avec le lien renvoyé pour la commande. 

## Fonctionnement 

Notre projet est constitué de 2 dossiers principaux :

### Scraper : le scraping

Ce dossier constitue le moteur de données du projet. Son rôle est de naviguer sur le web, d'extraire les informations pertinentes du site Ubisoft et de les transformer pour ainsi, mieux les exploiter par la suite. 

#### main.py : Fichier principal

Le script est divisé en plusieurs étapes clés pour transformer la page web brute en une base de données structurée : 

1 - On utilise la dépendance pymango pour se connecter à notre base de données. Par un lien dynamique, il récupère l'adresse de la base via une variable d'environnement MONGO_URI. 

2- De là, on utilise requests pour télécharger la page de l'Ubisoft Store et la méthode BeautifulSoup() pour l'analyser : 

-- On vient chercher des balises spécifiques "<script>" qui contiennent des objets JSON product. 

-- On vérifie également les attributs data-tc100 pour identifier si l'article est un jeu complet ou un contenu téléchargeable (DLC). 

3 - Après tout cela réalisé, on effectue un grand nettoyage des données, afin de pouvoir les exploiter dans un dashboard. Pour ce faire, nous avons implémenté plusieurs fonctions : 

-- normalize_genre() : Fonction qui vient traduire les genres des jeux parsés du français à l'anglais. Ce choix est effectué pour un souci d'uniformisation et de clarté. 

-- parse_price() : Fonction qui convertit certaines chaînes de caractères en nombres flottants de type float. On peut alors gérer les cas de jeux "Gratuits" pour les définir à 0. 

-- filter_on_sale_games() : Fonction qui calcule le pourcentage de réduction pour un jeu en promotion. 

4 - Une fois ces étapes terminés, on obtient alors un scraping complet de la page web. 

### App : le dashboard

Ce dossier constitue l'interface utilisateur du projet. Son but est de transformer les données brutes stockées dans MongoDB en un tableau de bord visuel et interactif pour l'utilisateur final.

#### main.py : Fichier principal

C'est le fichier central qui gère l'affichage et l'interaction. Il remplit plusieurs fonctions critiques :

1 - Le script utilise un décorateur @st.cache_resource pour la fonction init_connection(). Cela permet d'établir la connexion à MongoDB une seule fois pour toute la durée de vie de l'application, évitant ainsi de ralentir l'interface à chaque clic de l'utilisateur.

2 - Il récupère les données de la collection games et les transforme en un DataFrame pandas pour faciliter les manipulations.

3 - On définit une sidebar afin de filtrer par nom, prix, jeux en promotion ou encore les genres et afin afficher les données qui nous intéressent. Le script génère également des indicateurs clés comme le prix moyen et le nombre total de jeux, ainsi que des graphiques interactifs (via plotly) pour montrer la répartition par genre et la distribution des prix. 


==> L'objectif principal de ce dossier est de fournir une expérience utilisateur (UX) fluide. Alors que le scraper s'occupe de la technique et de la donnée brute, ce module app se concentre sur la valeur métier : permettre à un utilisateur de trouver rapidement les meilleures promotions ou les jeux d'un genre spécifique parmi des centaines d'entrées.

## Bonus : Docker-compose

On peut aller encore plus loin avec ce projet. En effet, toutes les étapes effectuées jusqu'à présent sont certes efficaces, mais nécéssitent un lancement manuel ordonnée afin de pouvoir ouvrir le dashboard ( MongoDB --> Scraper --> App). Ce processus n'est pas ergonomique et pourrait cumuler à plusieurs erreurs de lancement dans les différentes étapes. 

C'est pourquoi on décide d'ajouter un fichier docker-compose. Cette composante dite "multi-service" va permettre non lancer d'automatiser notre dashboard grâce une seule commande, mais aussi à garder en mémoire nos jeux scrappés. 

### Services

On fait appel au différents services : mongo pour la base de données, scraper pour extraire, et app pour lancer le dashboard. 

Avec cette structure, votre projet répond parfaitement aux exigences professionnelles : isolation, reproductibilité et facilité de déploiement.
