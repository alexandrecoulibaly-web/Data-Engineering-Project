<h1 align="center"> Ubisoft Scraper & Dashboard</h1>

<p align="center"><img src="https://purepng.com/public/uploads/large/purepng.com-ubisoft-logo-oldlogosubisoft-821523994680q5xlc.png" width="200"></p>

Ce projet a pour objectif de collecter, stocker et visualiser les données des jeux du catalogue <strong>Ubisoft Store France </strong> (https://store.ubisoft.com/fr/games). Tout ceci sera affiché via une <strong>application interactive. </strong> 
Il s'appuie sur une architectre de conteneurs pour garantir la portabilité et la modularité des services.

## Choix techniques

La conception de ce projet s'est faite sur une stack technologique moderne : 

--> Pour le développement du scraper et l'interface utilisateur, nous avons opté pour le langage Python. Ce choix a facilité la maintenance et la partage de bibilothèques entre différents modules. On a pu également utiliser la framework Streamlit afin de concevoir rapidement des scripts Python en applications web interactives.

--> Concernant le stockage des informations, nous utilisons MongoDB. Cette base de données de type NoSQL a été privilégiée pour sa flexibilité. On peut ainsi gérer un ensemble de données variables, ce qui est essentiel ici puisque certains jeux extraits possèdent des métadonnées plus riches. 

--> Enfin, l'intégralité de la solution est pilotée par Docker et Docker-Compose. Cela permet l'orchestration de 3 services essentiels : le moteur de scraping, la base de données et l'application. 
-- Docker & Docker-Compose : Orchestration de trois services (Scraper, Database, App) pour un déploiement "one-click". On garantit l'adaptabilité du projet sur n'importe quelle machine, offrant ainsi un déploiement "one-click" rapide et sans erreurs de configuration. 

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

==> On reste sur une architecture simple : 2 dossiers principaux composé d'un fichier principal <strong>main.py</strong> , d'une composante <strong>Dockerfile</strong>  et d'un fichier texte <strong>requirements.txt</strong> , regroupant les dépendances nécessaires à installer pour le fonctionnement du code. 

## Installation 

Pour pouvoir lancer le scraping et l'application : 

<strong>1</strong>  - Assurez vous d'avoir installé et configuré Docker. 

<strong>2</strong>  - Cloner le projet dans votre environnement local : 

<div class="highlight"><pre><span></span>$ git clone https://github.com/<Nom-du-repo>/Data-Engineering-Project.git
</pre></div>

<strong>3</strong>  - Lancer l'environnement : 

<div class="highlight"><pre><span></span>$ docker-compose up --build
</pre></div>

Cette commande lancera automatiquement la base de données MongoDB, exécute le scraper et démarre l'interface Streamlit. 

<strong>4</strong>  - Rendez vous sur Dockerfile et assurez vous que vos conteneurs tournent. Accédez au dashboard sur un navigateur avec le lien renvoyé par le conteneur "app" sur Dockerfile. 

## Fonctionnement 

Notre projet est constitué de <strong>2 dossiers principaux :</strong>

### Scraper : le scraping

Ce dossier constitue le moteur de données du projet. Son rôle est de naviguer sur le web, d'extraire les informations pertinentes du site Ubisoft et de les transformer pour ainsi, mieux les exploiter par la suite. 

#### main.py : Fichier principal

Le script est divisé en plusieurs étapes clés pour transformer la page web brute en une base de données structurée : 

<strong>1</strong> - On utilise la dépendance <i>pymango</i> pour se connecter à notre base de données. Par un lien dynamique, il récupère l'adresse de la base via une <strong>variable d'environnement MONGO_URI</strong>. 

<strong>2</strong>- De là, on utilise <i>requests</i> pour télécharger la page de l'Ubisoft Store et la méthode <i>BeautifulSoup()</i> pour l'analyser : 

<i>--> On vient chercher des balises spécifiques <strong>"<script>"</strong> qui contiennent des objets JSON product.</i> 

<i>--> On vérifie également les <strong>attributs data-tc100</strong> pour identifier si l'article est un jeu complet ou un contenu téléchargeable (DLC). </i>

<strong>3</strong> - Après tout cela réalisé, on effectue un grand nettoyage des données, afin de pouvoir les exploiter dans un dashboard. Pour ce faire, nous avons implémenté plusieurs <strong>fonctions :</strong>

<i>--> <strong>normalize_genre()</strong> : Fonction qui vient traduire les genres des jeux parsés du français à l'anglais. Ce choix est effectué pour un souci d'uniformisation et de clarté. </i>

<i>--> <strong>parse_price()</strong> : Fonction qui convertit certaines chaînes de caractères en nombres flottants de type float. On peut alors gérer les cas de jeux "Gratuits" pour les définir à 0. </i>

<i>--> <strong>filter_on_sale_games()</strong> : Fonction qui calcule le pourcentage de réduction pour un jeu en promotion. </i>

<strong>4</strong>- Une fois ces étapes terminés, on obtient alors un scraping complet de la page web. 

### App : le dashboard

Ce dossier constitue l'interface utilisateur du projet. Son but est de transformer les données brutes stockées dans MongoDB en un tableau de bord visuel et interactif pour l'utilisateur final.

#### main.py : Fichier principal

C'est le fichier central qui gère l'affichage et l'interaction. Il remplit plusieurs fonctions critiques :

<strong>1</strong> - Le script utilise un décorateur <strong>@st.cache_resource</strong> pour la fonction <i>init_connection()</i>. Cela permet d'établir la connexion à MongoDB une seule fois pour toute la durée de vie de l'application, évitant ainsi de ralentir l'interface à chaque clic de l'utilisateur.

<strong>2</strong> - On récupère les données de la collection games et les transforme en un DataFrame pandas pour faciliter les manipulations.

<strong>3</strong> - On définit une sidebar afin de filtrer par nom, prix, jeux en promotion ou encore les genres et afin afficher les données qui nous intéressent. Le script génère également des indicateurs clés comme le prix moyen et le nombre total de jeux, ainsi que des graphiques interactifs <i>(via plotly)</i> pour montrer la répartition par genre et la distribution des prix. 


<i><strong>==> L'objectif principal de ce dossier est de fournir une expérience utilisateur fluide. Alors que le scraper s'occupe de la technique et de la donnée brute, ce module app se concentre sur la valeur métier : permettre à un utilisateur de trouver rapidement les meilleures promotions ou les jeux d'un genre spécifique parmi des centaines d'entrées.</strong></i>

## Bonus : Docker-compose

On peut aller encore plus loin avec ce projet. En effet, toutes les étapes effectuées jusqu'à présent sont certes efficaces, mais nécéssitent un <strong>lancement manuel ordonné</strong> afin de pouvoir ouvrir le dashboard ( MongoDB --> Scraper --> App). Ce processus n'est pas <strong>ergonomique</strong> et pourrait cumuler plusieurs risques d'erreurs dans les différentes étapes. 

C'est pourquoi on décide d'ajouter un fichier <strong>docker-compose</strong>. Cette composante dite "multi-service" va permettre non lancer d'automatiser notre dashboard grâce à <strong>une seule commande</strong>, mais aussi à garder en mémoire nos jeux scrappés. 

On fait alors appel au différents services : mongo pour la base de données, scraper pour extraire, et app pour lancer le dashboard. 

Avec cette structure, votre projet répond parfaitement aux exigences professionnelles : isolation, reproductibilité et facilité de déploiement.
