from twitter_client import TwitterClient
import argparse

test_tweets = [
  {
    "titles": [
      "RDC : encore des Chinois arrêtés au Sud-Kivu, cette fois avec 12 lingots d’or et 800 000 dollars | Actualite.cd",
      "Exploitation illégale des minerais : encore 3 Chinois arrêtés avec des lingots d'or et des centaines de milliers de USD au Sud-Kivu"
    ],
    "urls": [
      "https://actualite.cd/2025/01/05/rdc-encore-des-chinois-arretes-au-sud-kivu-cette-fois-avec-12-lingots-dor-et-800-000",
      "https://www.mediacongo.net/article-actualite-145996_exploitation_illegale_des_minerais_encore_3_chinois_arretes_avec_des_lingots_d_or_et_des_centaines_de_milliers_de_usd_au_sud_kivu.html"
    ],
    "summary": "Titre: Arrestation de Chinois en République Démocratique du Congo pour exploitation illégale d'or\n\nRésumé: Les forces de sécurité du Sud-Kivu ont intercepté trois Chinois avec des lingots d'or et une somme d'argent améliore dans un village de Mashango. Ces arrestations, qui ont été saluées par la société civile, sont le deuxième groupe de Chinois arrêtés pour activités similaires. L'arrestation a été effectuée après l'expulsion des mêmes hommes de la DGM -Direction Générale de Migration- quelques jours plus tard."
  },
  {
    "titles": [
      "RDC : Une importante donation de réactifs et équipements pour intensifier la lutte contre le Mpox | Actualite.cd",
      "Santé – Lutte contre Mpox : La RDC bénéficie des réactifs et équipements médicaux pour la riposte"
    ],
    "urls": [
      "https://actualite.cd/2025/01/05/rdc-une-importante-donation-de-reactifs-et-equipements-pour-intensifier-la-lutte-contre",
      "https://depeche.cd/2025/01/05/sante-lutte-contre-mpox-la-rdc-beneficie-des-reactifs-et-equipements-medicaux-pour-la-riposte/"
    ],
    "summary": "Titre: Don de médicaments et équipements médicaux contre la maladie Mpox en République démocratique du Congo\n\nRésumé:\nLe président Félix Tshisekedi a inauguré une cérémonie à l'Institut national des recherches biomédicales (INRB) pour la remise officielle de reagents et d'équipements de laboratoire. Ce don, fourni par le Centre africain de contrôle et de prévention des maladies (Africa CDC), s'ajoute aux véhicules neufs mis à disposition par le gouvernement congolais. Le directeur général de l'Institut national de santé publique a souligné des avancées dans la riposte contre la maladie, notamment une augmentation du nombre de cas suspects, une amélioration de la détection biologique et une diminution de la mortalité. Le directeur général de l'Africa CDC a remercié le président Tshisekedi pour son engagement. L'Institut national des recherches biomédicales a servi de cadre à la cérémonie, qui a été présidée par le chef de l'État."
  }
]

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="A script that accepts command-line arguments.")

    # Define a command-line argument --environment
    parser.add_argument('--environment', type=str, help='Specify the environment (development or production)', required=True)

    # Parse the arguments
    args = parser.parse_args()

    # Access the --environment argument | Should be either 'local' or 'production'
    environment = args.environment 

    # Logic based on the environment value
    client = TwitterClient()
    client.tweet_all(test_tweets,env=environment)

if __name__ == "__main__":
    main()
