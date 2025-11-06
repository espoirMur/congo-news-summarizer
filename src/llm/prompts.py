SUMMARIZATION_PROMPT_TEMPLATE = """
Donnez un titre et un court résumé de 2 à 3 phrases en français des documents suivant :
{{content}}
 Décrivez-le dans le style d'un journaliste de presse française qui ecrit une revue de presse.

Ne résumez pas chaque document séparément, le contenu de tous les documents doit être résumé ensemble.

Le titre et le résumé doivent être en français et non en anglais.
"""
