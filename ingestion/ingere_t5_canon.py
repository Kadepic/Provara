"""
INGESTION T5 — CANON ŒUVRES (compositeur d'opéra / de comédie musicale) DEPUIS LA CONNAISSANCE DU MODÈLE.

Pourquoi cette voie : Wikidata FR est SOUS-PEUPLÉE sur les classes d'œuvres fines (scout 2026-06-26 :
opéra Q1344 = 22 entités, comédie musicale Q2743 = 6) alors que le RÉPERTOIRE RÉEL en compte des centaines.
Sur autorisation de Yohan (2026-06-26 : « tu as été entraîné donc tu peux même être la source si besoin »),
on comble ce trou avec le CANON UNIVERSELLEMENT ÉTABLI — des faits FIXÉS PAR LA RÉALITÉ que le modèle connaît
avec quasi-certitude (Verdi a composé La Traviata ; ce n'est pas en débat).

GARDE-FOUS FAUX=0 (inchangés) :
  • SOURCE ÉTIQUETÉE HONNÊTEMENT « connaissance modèle (Claude) » -> auditable + réversible (on peut plus tard
    re-vérifier chaque ligne contre une source externe sans la confondre avec du Wikidata).
  • CANON SEULEMENT : on n'inscrit qu'une attribution INDISCUTABLE. Au moindre doute -> on n'écrit pas.
  • UN SEUL compositeur par œuvre (relation fonctionnelle) : les œuvres à compositeur multiple/disputé ou les
    duos (ABBA, Pasek & Paul…) sont ÉCARTÉS, sauf crédit combiné canonique unique. Sondheim n'est inscrit que
    pour les œuvres dont il est le COMPOSITEUR (pas West Side Story / Gypsy où il n'est que parolier).
  • `publie()` applique en plus : `fonctionnel` (toute clé multi-valeur -> HORS) + réconciliation amorce
    (conflit avec un fait déjà connu -> datasets/_conflits/, JAMAIS d'écrasement silencieux).

Usage : python3 ingere_t5_canon.py        (offline, aucune requête réseau)
"""
from __future__ import annotations

from ingere_wikidata import publie

SRC = ("connaissance modèle (Claude) — canon haute-confiance (Wikidata FR sous-peuplée : "
       "opéra 22 / comédie musicale 6 entités au 2026-06-26)")

# ── COMPOSITEUR D'OPÉRA — titre dans la langue/forme la plus reconnue ────────────────────────────
OPERAS = [
    # Verdi
    ("La traviata", "Giuseppe Verdi"), ("Rigoletto", "Giuseppe Verdi"),
    ("Il trovatore", "Giuseppe Verdi"), ("Aida", "Giuseppe Verdi"),
    ("Otello", "Giuseppe Verdi"), ("Falstaff", "Giuseppe Verdi"),
    ("Nabucco", "Giuseppe Verdi"), ("Macbeth", "Giuseppe Verdi"),
    ("Un ballo in maschera", "Giuseppe Verdi"), ("La forza del destino", "Giuseppe Verdi"),
    ("Don Carlos", "Giuseppe Verdi"), ("Simon Boccanegra", "Giuseppe Verdi"),
    ("Luisa Miller", "Giuseppe Verdi"), ("Ernani", "Giuseppe Verdi"),
    ("Les vêpres siciliennes", "Giuseppe Verdi"),
    # Mozart
    ("Le nozze di Figaro", "Wolfgang Amadeus Mozart"), ("Don Giovanni", "Wolfgang Amadeus Mozart"),
    ("Die Zauberflöte", "Wolfgang Amadeus Mozart"), ("Così fan tutte", "Wolfgang Amadeus Mozart"),
    ("Idomeneo", "Wolfgang Amadeus Mozart"), ("La clemenza di Tito", "Wolfgang Amadeus Mozart"),
    ("Die Entführung aus dem Serail", "Wolfgang Amadeus Mozart"),
    # Puccini
    ("La Bohème", "Giacomo Puccini"), ("Tosca", "Giacomo Puccini"),
    ("Madama Butterfly", "Giacomo Puccini"), ("Turandot", "Giacomo Puccini"),
    ("Manon Lescaut", "Giacomo Puccini"), ("Gianni Schicchi", "Giacomo Puccini"),
    ("Il tabarro", "Giacomo Puccini"), ("Suor Angelica", "Giacomo Puccini"),
    ("La fanciulla del West", "Giacomo Puccini"), ("La rondine", "Giacomo Puccini"),
    # Wagner
    ("Tristan und Isolde", "Richard Wagner"), ("Die Walküre", "Richard Wagner"),
    ("Das Rheingold", "Richard Wagner"), ("Siegfried", "Richard Wagner"),
    ("Götterdämmerung", "Richard Wagner"), ("Parsifal", "Richard Wagner"),
    ("Lohengrin", "Richard Wagner"), ("Tannhäuser", "Richard Wagner"),
    ("Der fliegende Holländer", "Richard Wagner"),
    ("Die Meistersinger von Nürnberg", "Richard Wagner"),
    # Rossini
    ("Il barbiere di Siviglia", "Gioachino Rossini"), ("La Cenerentola", "Gioachino Rossini"),
    ("Guillaume Tell", "Gioachino Rossini"), ("L'italiana in Algeri", "Gioachino Rossini"),
    ("La gazza ladra", "Gioachino Rossini"), ("Semiramide", "Gioachino Rossini"),
    ("Il turco in Italia", "Gioachino Rossini"), ("Tancredi", "Gioachino Rossini"),
    # Donizetti
    ("Lucia di Lammermoor", "Gaetano Donizetti"), ("L'elisir d'amore", "Gaetano Donizetti"),
    ("Don Pasquale", "Gaetano Donizetti"), ("La fille du régiment", "Gaetano Donizetti"),
    ("Anna Bolena", "Gaetano Donizetti"), ("Maria Stuarda", "Gaetano Donizetti"),
    ("Roberto Devereux", "Gaetano Donizetti"), ("Lucrezia Borgia", "Gaetano Donizetti"),
    # Bellini
    ("Norma", "Vincenzo Bellini"), ("I puritani", "Vincenzo Bellini"),
    ("La sonnambula", "Vincenzo Bellini"), ("Il pirata", "Vincenzo Bellini"),
    ("I Capuleti e i Montecchi", "Vincenzo Bellini"),
    # Bizet / Gounod / Massenet / Saint-Saëns / Berlioz / Offenbach (français)
    ("Carmen", "Georges Bizet"), ("Les pêcheurs de perles", "Georges Bizet"),
    ("Faust", "Charles Gounod"), ("Roméo et Juliette", "Charles Gounod"),
    ("Manon", "Jules Massenet"), ("Werther", "Jules Massenet"),
    ("Thaïs", "Jules Massenet"), ("Don Quichotte", "Jules Massenet"),
    ("Samson et Dalila", "Camille Saint-Saëns"),
    ("Les Troyens", "Hector Berlioz"), ("La Damnation de Faust", "Hector Berlioz"),
    ("Les Contes d'Hoffmann", "Jacques Offenbach"), ("Orphée aux enfers", "Jacques Offenbach"),
    ("La belle Hélène", "Jacques Offenbach"),
    ("Pelléas et Mélisande", "Claude Debussy"),
    ("Dialogues des carmélites", "Francis Poulenc"), ("La voix humaine", "Francis Poulenc"),
    ("L'enfant et les sortilèges", "Maurice Ravel"), ("L'heure espagnole", "Maurice Ravel"),
    # Handel (baroque)
    ("Giulio Cesare", "Georg Friedrich Haendel"), ("Rinaldo", "Georg Friedrich Haendel"),
    ("Alcina", "Georg Friedrich Haendel"), ("Rodelinda", "Georg Friedrich Haendel"),
    ("Ariodante", "Georg Friedrich Haendel"), ("Serse", "Georg Friedrich Haendel"),
    # Monteverdi / Gluck / Purcell (baroque/classique)
    ("L'Orfeo", "Claudio Monteverdi"), ("L'incoronazione di Poppea", "Claudio Monteverdi"),
    ("Orfeo ed Euridice", "Christoph Willibald Gluck"), ("Iphigénie en Tauride", "Christoph Willibald Gluck"),
    ("Dido and Aeneas", "Henry Purcell"),
    # Richard Strauss
    ("Der Rosenkavalier", "Richard Strauss"), ("Salome", "Richard Strauss"),
    ("Elektra", "Richard Strauss"), ("Ariadne auf Naxos", "Richard Strauss"),
    ("Die Frau ohne Schatten", "Richard Strauss"),
    # Beethoven / Weber / Humperdinck (allemand)
    ("Fidelio", "Ludwig van Beethoven"),
    ("Der Freischütz", "Carl Maria von Weber"),
    ("Hänsel und Gretel", "Engelbert Humperdinck"),
    # Russe
    ("Eugène Onéguine", "Piotr Ilitch Tchaïkovski"), ("La Dame de pique", "Piotr Ilitch Tchaïkovski"),
    ("Boris Godounov", "Modeste Moussorgski"), ("La Khovanchtchina", "Modeste Moussorgski"),
    ("Le Prince Igor", "Alexandre Borodine"),
    ("Le Coq d'or", "Nikolaï Rimski-Korsakov"),
    # Vérisme / italien post-Verdi
    ("Pagliacci", "Ruggero Leoncavallo"), ("Cavalleria rusticana", "Pietro Mascagni"),
    ("La Gioconda", "Amilcare Ponchielli"), ("Andrea Chénier", "Umberto Giordano"),
    ("Adriana Lecouvreur", "Francesco Cilea"),
    # Tchèque
    ("Rusalka", "Antonín Dvořák"), ("Jenůfa", "Leoš Janáček"),
    ("La Petite Renarde rusée", "Leoš Janáček"), ("La Fiancée vendue", "Bedřich Smetana"),
    # XXe siècle
    ("The Rake's Progress", "Igor Stravinsky"),
    ("Wozzeck", "Alban Berg"), ("Lulu", "Alban Berg"),
    ("Peter Grimes", "Benjamin Britten"), ("Billy Budd", "Benjamin Britten"),
    ("The Turn of the Screw", "Benjamin Britten"),
    ("Le Château de Barbe-Bleue", "Béla Bartók"),
    ("Porgy and Bess", "George Gershwin"),
    ("Nixon in China", "John Adams"), ("Doctor Atomic", "John Adams"),
    ("Einstein on the Beach", "Philip Glass"), ("Akhnaten", "Philip Glass"),
    ("Satyagraha", "Philip Glass"),
    # — expansion canon (2026-06-26) : baroque français, opérette, vérisme, russe, tchèque, XXe —
    ("Les Indes galantes", "Jean-Philippe Rameau"), ("Castor et Pollux", "Jean-Philippe Rameau"),
    ("Hippolyte et Aricie", "Jean-Philippe Rameau"),
    ("Armide", "Jean-Baptiste Lully"), ("Atys", "Jean-Baptiste Lully"),
    ("Die Fledermaus", "Johann Strauss II"),
    ("La Veuve joyeuse", "Franz Lehár"),
    ("La Périchole", "Jacques Offenbach"),
    ("Cendrillon (Massenet)", "Jules Massenet"), ("Le Cid", "Jules Massenet"),
    ("Louise", "Gustave Charpentier"), ("Ariane et Barbe-Bleue", "Paul Dukas"),
    ("La Wally", "Alfredo Catalani"), ("Mefistofele", "Arrigo Boito"),
    ("Oberon", "Carl Maria von Weber"),
    ("La Fille de neige", "Nikolaï Rimski-Korsakov"), ("Sadko", "Nikolaï Rimski-Korsakov"),
    ("L'Amour des trois oranges", "Sergueï Prokofiev"), ("Guerre et Paix", "Sergueï Prokofiev"),
    ("Lady Macbeth de Mtsensk", "Dmitri Chostakovitch"),
    ("Katia Kabanova", "Leoš Janáček"), ("L'Affaire Makropoulos", "Leoš Janáček"),
    ("Dalibor", "Bedřich Smetana"), ("Halka", "Stanisław Moniuszko"),
    ("Giovanna d'Arco", "Giuseppe Verdi"), ("I due Foscari", "Giuseppe Verdi"),
    ("A Midsummer Night's Dream", "Benjamin Britten"), ("Death in Venice", "Benjamin Britten"),
    # — expansion 2 (2026-06-26) : opéras certains, sans homonyme déjà présent (pas d'Otello/Armide/Alceste) —
    ("I masnadieri", "Giuseppe Verdi"), ("Stiffelio", "Giuseppe Verdi"), ("Oberto", "Giuseppe Verdi"),
    ("La Favorite", "Gaetano Donizetti"),
    ("Le Comte Ory", "Gioachino Rossini"), ("La donna del lago", "Gioachino Rossini"),
    ("Hérodiade", "Jules Massenet"), ("Esclarmonde", "Jules Massenet"),
    ("Mireille", "Charles Gounod"),
    ("La Vie parisienne", "Jacques Offenbach"),
    ("La Grande-Duchesse de Gérolstein", "Jacques Offenbach"),
    ("Orlando", "Georg Friedrich Haendel"), ("Semele", "Georg Friedrich Haendel"),
    ("Iphigénie en Aulide", "Christoph Willibald Gluck"),
    ("Platée", "Jean-Philippe Rameau"), ("Dardanus", "Jean-Philippe Rameau"),
    ("Capriccio", "Richard Strauss"), ("Arabella", "Richard Strauss"),
    ("Iolanta", "Piotr Ilitch Tchaïkovski"),
    ("Mozart et Salieri", "Nikolaï Rimski-Korsakov"),
    ("Rienzi", "Richard Wagner"), ("Benvenuto Cellini", "Hector Berlioz"),
    ("Albert Herring", "Benjamin Britten"), ("L'Ange de feu", "Sergueï Prokofiev"),
    ("Euryanthe", "Carl Maria von Weber"),
    ("Les Joyeuses Commères de Windsor", "Otto Nicolai"), ("Martha", "Friedrich von Flotow"),
    ("Mignon", "Ambroise Thomas"), ("Lakmé", "Léo Delibes"),
    ("La Jolie Fille de Perth", "Georges Bizet"),
    # — expansion saturation (2026-06-26 loop) : opéras à compositeur unique, sans homonyme déjà présent —
    ("Attila", "Giuseppe Verdi"), ("Alzira", "Giuseppe Verdi"), ("Il corsaro", "Giuseppe Verdi"),
    ("La battaglia di Legnano", "Giuseppe Verdi"), ("Aroldo", "Giuseppe Verdi"),
    ("Mitridate, re di Ponto", "Wolfgang Amadeus Mozart"), ("Lucio Silla", "Wolfgang Amadeus Mozart"),
    ("La finta giardiniera", "Wolfgang Amadeus Mozart"), ("Il re pastore", "Wolfgang Amadeus Mozart"),
    ("Tamerlano", "Georg Friedrich Haendel"), ("Teseo", "Georg Friedrich Haendel"),
    ("Agrippina", "Georg Friedrich Haendel"), ("Partenope", "Georg Friedrich Haendel"),
    ("Berenice", "Georg Friedrich Haendel"), ("Tolomeo", "Georg Friedrich Haendel"),
    ("Daphne", "Richard Strauss"), ("Intermezzo", "Richard Strauss"),
    ("Die ägyptische Helena", "Richard Strauss"), ("Die schweigsame Frau", "Richard Strauss"),
    ("Guntram", "Richard Strauss"), ("Feuersnot", "Richard Strauss"),
    ("Mazeppa", "Piotr Ilitch Tchaïkovski"), ("L'Enchanteresse", "Piotr Ilitch Tchaïkovski"),
    ("La Fiancée du tsar", "Nikolaï Rimski-Korsakov"),
    ("La Légende de la ville invisible de Kitège", "Nikolaï Rimski-Korsakov"),
    ("La Reine de Saba", "Charles Gounod"), ("Le Médecin malgré lui", "Charles Gounod"),
    ("Philémon et Baucis", "Charles Gounod"), ("La Nonne sanglante", "Charles Gounod"),
    ("Le jongleur de Notre-Dame", "Jules Massenet"), ("Grisélidis", "Jules Massenet"),
    ("Linda di Chamounix", "Gaetano Donizetti"), ("Poliuto", "Gaetano Donizetti"),
    ("Belisario", "Gaetano Donizetti"), ("Caterina Cornaro", "Gaetano Donizetti"),
    ("Gloriana", "Benjamin Britten"), ("The Rape of Lucretia", "Benjamin Britten"),
    ("Owen Wingrave", "Benjamin Britten"),
    ("Le Joueur", "Sergueï Prokofiev"), ("Les Fiançailles au couvent", "Sergueï Prokofiev"),
    ("Les Deux Veuves", "Bedřich Smetana"), ("Libuše", "Bedřich Smetana"),
    ("Une vie pour le tsar", "Mikhaïl Glinka"), ("Rouslan et Ludmila", "Mikhaïl Glinka"),
    ("Béatrice et Bénédict", "Hector Berlioz"), ("Djamileh", "Georges Bizet"),
    ("Le Diable et Catherine", "Antonín Dvořák"), ("Dimitrij", "Antonín Dvořák"),
    # — expansion saturation round 3 (2026-06-26 loop) : grand opéra français, vérisme, russes, Handel —
    ("Les Huguenots", "Giacomo Meyerbeer"), ("Le Prophète", "Giacomo Meyerbeer"),
    ("L'Africaine", "Giacomo Meyerbeer"), ("Robert le diable", "Giacomo Meyerbeer"),
    ("Dinorah", "Giacomo Meyerbeer"),
    ("La Muette de Portici", "Daniel-François-Esprit Auber"), ("Fra Diavolo", "Daniel-François-Esprit Auber"),
    ("Le Domino noir", "Daniel-François-Esprit Auber"),
    ("La Juive", "Fromental Halévy"), ("La Vestale", "Gaspare Spontini"),
    ("Les Deux Journées", "Luigi Cherubini"),
    ("Dom Sébastien", "Gaetano Donizetti"), ("Il campanello", "Gaetano Donizetti"),
    ("L'assedio di Calais", "Gaetano Donizetti"),
    ("Elisabetta, regina d'Inghilterra", "Gioachino Rossini"), ("Maometto II", "Gioachino Rossini"),
    ("Zelmira", "Gioachino Rossini"), ("Ermione", "Gioachino Rossini"),
    ("Le Roi de Lahore", "Jules Massenet"), ("Chérubin", "Jules Massenet"), ("Roma", "Jules Massenet"),
    ("L'arlesiana", "Francesco Cilea"), ("Fedora", "Umberto Giordano"),
    ("L'amico Fritz", "Pietro Mascagni"), ("Iris", "Pietro Mascagni"), ("Zazà", "Ruggero Leoncavallo"),
    ("Il segreto di Susanna", "Ermanno Wolf-Ferrari"), ("I quatro rusteghi", "Ermanno Wolf-Ferrari"),
    ("La Pucelle d'Orléans", "Piotr Ilitch Tchaïkovski"), ("Cherevichki", "Piotr Ilitch Tchaïkovski"),
    ("La Nuit de mai", "Nikolaï Rimski-Korsakov"), ("La Foire de Sorotchintsy", "Modeste Moussorgski"),
    ("Semyon Kotko", "Sergueï Prokofiev"),
    ("Ottone", "Georg Friedrich Haendel"), ("Flavio", "Georg Friedrich Haendel"),
    ("Floridante", "Georg Friedrich Haendel"), ("Scipione", "Georg Friedrich Haendel"),
    ("Curlew River", "Benjamin Britten"), ("Noye's Fludde", "Benjamin Britten"),
    # — expansion saturation round 5 (2026-06-26 loop) : baroque, bel canto, XXe ; homonymes écartés —
    ("Orlando furioso", "Antonio Vivaldi"), ("Farnace", "Antonio Vivaldi"),
    ("La serva padrona", "Giovanni Battista Pergolesi"), ("Lo frate 'nnamorato", "Giovanni Battista Pergolesi"),
    ("Il matrimonio segreto", "Domenico Cimarosa"),
    ("La Calisto", "Francesco Cavalli"), ("Giasone", "Francesco Cavalli"), ("L'Ormindo", "Francesco Cavalli"),
    ("David et Jonathas", "Marc-Antoine Charpentier"),
    ("Phaëton", "Jean-Baptiste Lully"), ("Persée", "Jean-Baptiste Lully"),
    ("Cadmus et Hermione", "Jean-Baptiste Lully"), ("Roland", "Jean-Baptiste Lully"),
    ("Les Boréades", "Jean-Philippe Rameau"), ("Zoroastre", "Jean-Philippe Rameau"),
    ("Paride ed Elena", "Christoph Willibald Gluck"),
    ("Imeneo", "Georg Friedrich Haendel"), ("Deidamia", "Georg Friedrich Haendel"),
    ("Riccardo Primo", "Georg Friedrich Haendel"), ("Lotario", "Georg Friedrich Haendel"),
    ("Sosarme", "Georg Friedrich Haendel"), ("Faramondo", "Georg Friedrich Haendel"),
    ("Il ritorno d'Ulisse in patria", "Claudio Monteverdi"),
    ("The Fairy-Queen", "Henry Purcell"),
    ("Doktor Faust", "Ferruccio Busoni"), ("Cardillac", "Paul Hindemith"),
    ("Mathis der Maler", "Paul Hindemith"), ("Moses und Aron", "Arnold Schönberg"),
    ("Die tote Stadt", "Erich Wolfgang Korngold"), ("Palestrina", "Hans Pfitzner"),
    ("Le Grand Macabre", "György Ligeti"), ("Saint François d'Assise", "Olivier Messiaen"),
    # — expansion saturation round 16 (2026-06-26 run autonome) : opéras à compositeur UNIQUE (gap-filtrés vs existant) —
    ("La favorite", "Gaetano Donizetti"), ("Parisina", "Gaetano Donizetti"),
    ("Le comte Ory", "Gioachino Rossini"), ("Mosè in Egitto", "Gioachino Rossini"),
    ("Le siège de Corinthe", "Gioachino Rossini"),
    ("La straniera", "Vincenzo Bellini"), ("Zaira", "Vincenzo Bellini"),
    ("Don Quichotte (Massenet)", "Jules Massenet"), ("Sapho", "Jules Massenet"),
    ("Jérusalem", "Giuseppe Verdi"), ("Un giorno di regno", "Giuseppe Verdi"),
    ("Edgar", "Giacomo Puccini"), ("Le Villi", "Giacomo Puccini"),
    ("Kátia Kabanová", "Leoš Janáček"), ("De la maison des morts", "Leoš Janáček"),
    ("Le Songe d'une nuit d'été", "Benjamin Britten"),
    ("La Demoiselle des neiges", "Nikolaï Rimski-Korsakov"),
    # — expansion saturation round 38 (2026-06-27 run autonome, maintenance) : opéra à compositeur unique (gap-filtré coupes profondes) —
    ("Maria di Rohan", "Gaetano Donizetti"), ("Gemma di Vergy", "Gaetano Donizetti"),
    ("Marino Faliero", "Gaetano Donizetti"), ("Pia de' Tolomei", "Gaetano Donizetti"),
    ("Maria Padilla", "Gaetano Donizetti"), ("Armida", "Gioachino Rossini"),
    ("Matilde di Shabran", "Gioachino Rossini"), ("La scala di seta", "Gioachino Rossini"),
    ("Il signor Bruschino", "Gioachino Rossini"), ("Adelaide di Borgogna", "Gioachino Rossini"),
    ("Le roi de Lahore", "Jules Massenet"), ("Ariane", "Jules Massenet"),
    ("Cléopâtre", "Jules Massenet"), ("La Dame blanche", "François-Adrien Boieldieu"),
    # — expansion saturation round 41 (2026-06-27 run autonome, maintenance) : opéra baroque/classique, compositeur unique (gap-filtré) —
    ("Griselda", "Antonio Vivaldi"), ("Tito Manlio", "Antonio Vivaldi"), ("L'Olimpiade", "Antonio Vivaldi"),
    ("Catone in Utica", "Antonio Vivaldi"), ("Bajazet", "Antonio Vivaldi"), ("Dorilla in Tempe", "Antonio Vivaldi"),
    ("Alceste", "Christoph Willibald Gluck"), ("Armide (Gluck)", "Christoph Willibald Gluck"),
    ("Xerse", "Francesco Cavalli"), ("Ercole amante", "Francesco Cavalli"), ("La Didone", "Francesco Cavalli"),
    ("Ezio", "Georg Friedrich Haendel"), ("Arianna in Creta", "Georg Friedrich Haendel"),
    ("Atalanta", "Georg Friedrich Haendel"), ("Giustino", "Georg Friedrich Haendel"),
    ("Arminio", "Georg Friedrich Haendel"), ("La Griselda", "Alessandro Scarlatti"),
    ("Il Mitridate Eupatore", "Alessandro Scarlatti"), ("Cleofide", "Johann Adolph Hasse"),
    ("Artaserse", "Johann Adolph Hasse"),
    # — expansion saturation round 59 (2026-06-27 run autonome, maintenance) : opéra à compositeur unique (gap-filtré) —
    ("Le Nez", "Dmitri Chostakovitch"), ("La Vie pour le tsar", "Mikhaïl Glinka"), ("Le Jacobin", "Antonín Dvořák"),
    ("Julietta", "Bohuslav Martinů"), ("Vanessa", "Samuel Barber"), ("The Consul", "Gian Carlo Menotti"),
    ("Amahl and the Night Visitors", "Gian Carlo Menotti"), ("Punch and Judy", "Harrison Birtwistle"),
    ("The Tempest", "Thomas Adès"), ("Powder Her Face", "Thomas Adès"),
    ("The Midsummer Marriage", "Michael Tippett"), ("Susannah", "Carlisle Floyd"),
    # — expansion saturation round 79 (2026-06-28 run autonome, maintenance) : opéra XXe à compositeur unique (gap-filtré) —
    ("La Voix humaine", "Francis Poulenc"), ("Les Mamelles de Tirésias", "Francis Poulenc"),
    ("Le Rossignol", "Igor Stravinsky"), ("Erwartung", "Arnold Schönberg"), ("The Bassarids", "Hans Werner Henze"),
    ("Boulevard Solitude", "Hans Werner Henze"), ("Aufstieg und Fall der Stadt Mahagonny", "Kurt Weill"),
    ("Die Dreigroschenoper", "Kurt Weill"), ("Der Zwerg", "Alexander von Zemlinsky"), ("L'Heure espagnole", "Maurice Ravel"),
    # — expansion saturation round 95 (2026-06-28 run autonome, maintenance) : opéra bel canto coupes profondes, compositeur unique (gap-filtré) —
    ("Il diluvio universale", "Gaetano Donizetti"), ("Fausta", "Gaetano Donizetti"), ("Rosmonda d'Inghilterra", "Gaetano Donizetti"),
    ("Betly", "Gaetano Donizetti"), ("Le convenienze ed inconvenienze teatrali", "Gaetano Donizetti"),
    ("Aureliano in Palmira", "Gioachino Rossini"), ("Sigismondo", "Gioachino Rossini"), ("Torvaldo e Dorliska", "Gioachino Rossini"),
    ("Ciro in Babilonia", "Gioachino Rossini"), ("La cambiale di matrimonio", "Gioachino Rossini"),
    ("Médée", "Luigi Cherubini"), ("Lodoïska", "Luigi Cherubini"), ("Fernand Cortez", "Gaspare Spontini"),
    ("Olimpie", "Gaspare Spontini"), ("Il giuramento", "Saverio Mercadante"), ("Saffo", "Giovanni Pacini"),
    ("Adelson e Salvini", "Vincenzo Bellini"),
]

# ── COMPOSITEUR DE COMÉDIE MUSICALE — « music by » (parolier exclu si distinct) ──────────────────
MUSICALS = [
    # Andrew Lloyd Webber
    ("The Phantom of the Opera", "Andrew Lloyd Webber"), ("Cats", "Andrew Lloyd Webber"),
    ("Evita", "Andrew Lloyd Webber"), ("Jesus Christ Superstar", "Andrew Lloyd Webber"),
    ("Starlight Express", "Andrew Lloyd Webber"), ("Sunset Boulevard", "Andrew Lloyd Webber"),
    ("Joseph and the Amazing Technicolor Dreamcoat", "Andrew Lloyd Webber"),
    ("School of Rock", "Andrew Lloyd Webber"),
    # Stephen Sondheim (compositeur ET parolier de ces œuvres)
    ("Sweeney Todd", "Stephen Sondheim"), ("Into the Woods", "Stephen Sondheim"),
    ("Company", "Stephen Sondheim"), ("A Little Night Music", "Stephen Sondheim"),
    ("Sunday in the Park with George", "Stephen Sondheim"), ("Follies", "Stephen Sondheim"),
    ("Assassins", "Stephen Sondheim"),
    # Leonard Bernstein
    ("West Side Story", "Leonard Bernstein"), ("On the Town", "Leonard Bernstein"),
    ("Candide", "Leonard Bernstein"), ("Wonderful Town", "Leonard Bernstein"),
    # Richard Rodgers
    ("Oklahoma!", "Richard Rodgers"), ("Carousel", "Richard Rodgers"),
    ("South Pacific", "Richard Rodgers"), ("The King and I", "Richard Rodgers"),
    ("The Sound of Music", "Richard Rodgers"), ("Flower Drum Song", "Richard Rodgers"),
    # Claude-Michel Schönberg
    ("Les Misérables", "Claude-Michel Schönberg"), ("Miss Saigon", "Claude-Michel Schönberg"),
    # Jonathan Larson / Lin-Manuel Miranda
    ("Rent", "Jonathan Larson"),
    ("Hamilton", "Lin-Manuel Miranda"), ("In the Heights", "Lin-Manuel Miranda"),
    # Alan Menken
    ("Little Shop of Horrors", "Alan Menken"), ("Newsies", "Alan Menken"),
    # Frank Loesser
    ("Guys and Dolls", "Frank Loesser"),
    ("How to Succeed in Business Without Really Trying", "Frank Loesser"),
    # Jerry Bock / John Kander / Jerry Herman / Cy Coleman
    ("Fiddler on the Roof", "Jerry Bock"), ("She Loves Me", "Jerry Bock"),
    ("Cabaret", "John Kander"), ("Chicago", "John Kander"),
    ("Hello, Dolly!", "Jerry Herman"), ("Mame", "Jerry Herman"), ("La Cage aux Folles", "Jerry Herman"),
    ("Sweet Charity", "Cy Coleman"),
    # Stephen Schwartz / Marvin Hamlisch / Charles Strouse / Meredith Willson / Jule Styne
    ("Wicked", "Stephen Schwartz"), ("Godspell", "Stephen Schwartz"), ("Pippin", "Stephen Schwartz"),
    ("A Chorus Line", "Marvin Hamlisch"),
    ("Annie", "Charles Strouse"), ("Bye Bye Birdie", "Charles Strouse"),
    ("The Music Man", "Meredith Willson"),
    ("Gypsy", "Jule Styne"), ("Funny Girl", "Jule Styne"),
    # Galt MacDermot / Mel Brooks / Elton John
    ("Hair", "Galt MacDermot"),
    ("The Producers", "Mel Brooks"),
    ("Billy Elliot the Musical", "Elton John"),
    # — expansion canon (2026-06-26) : compositeurs uniques certains —
    ("Aspects of Love", "Andrew Lloyd Webber"),
    ("Pacific Overtures", "Stephen Sondheim"), ("Merrily We Roll Along", "Stephen Sondheim"),
    ("Passion", "Stephen Sondheim"),
    ("City of Angels", "Cy Coleman"), ("Barnum", "Cy Coleman"),
    ("Kiss of the Spider Woman", "John Kander"),
    ("Beauty and the Beast", "Alan Menken"), ("Aladdin", "Alan Menken"),
    ("Fun Home", "Jeanine Tesori"),
    # — expansion saturation round 2 (2026-06-26 loop) : compositeur unique « music by » (duos/trios écartés) —
    ("Once on This Island", "Stephen Flaherty"), ("Ragtime", "Stephen Flaherty"),
    ("Seussical", "Stephen Flaherty"), ("Anastasia", "Stephen Flaherty"),
    ("Dreamgirls", "Henry Krieger"), ("Memphis", "David Bryan"),
    ("Next to Normal", "Tom Kitt"), ("If/Then", "Tom Kitt"),
    ("Spring Awakening", "Duncan Sheik"),
    ("Caroline, or Change", "Jeanine Tesori"), ("Shrek the Musical", "Jeanine Tesori"),
    ("Thoroughly Modern Millie", "Jeanine Tesori"), ("Violet", "Jeanine Tesori"),
    ("9 to 5", "Dolly Parton"), ("Waitress", "Sara Bareilles"), ("Hadestown", "Anaïs Mitchell"),
    ("The Last Five Years", "Jason Robert Brown"), ("Parade", "Jason Robert Brown"),
    ("The Bridges of Madison County", "Jason Robert Brown"),
    ("Tick, Tick... Boom!", "Jonathan Larson"),
    ("Titanic", "Maury Yeston"), ("Nine", "Maury Yeston"),
    ("Sister Act", "Alan Menken"), ("The Hunchback of Notre Dame", "Alan Menken"),
    # — expansion saturation round 7 (2026-06-26 run autonome) : compositeur unique « music by » (duos écartés) —
    ("Whistle Down the Wind", "Andrew Lloyd Webber"), ("The Woman in White", "Andrew Lloyd Webber"),
    ("Love Never Dies", "Andrew Lloyd Webber"),
    ("Anyone Can Whistle", "Stephen Sondheim"), ("The Frogs", "Stephen Sondheim"),
    ("Mack and Mabel", "Jerry Herman"),
    ("Curtains", "John Kander"), ("The Scottsboro Boys", "John Kander"), ("The Visit", "John Kander"),
    ("On the Twentieth Century", "Cy Coleman"), ("Little Me", "Cy Coleman"),
    ("The Will Rogers Follies", "Cy Coleman"),
    ("Applause", "Charles Strouse"), ("Bells Are Ringing", "Jule Styne"),
    ("They're Playing Our Song", "Marvin Hamlisch"), ("The Goodbye Girl", "Marvin Hamlisch"),
    ("Children of Eden", "Stephen Schwartz"), ("The Magic Show", "Stephen Schwartz"),
    ("The Little Mermaid", "Alan Menken"), ("Leap of Faith", "Alan Menken"),
    ("Kimberly Akimbo", "Jeanine Tesori"),
    ("Honeymoon in Vegas", "Jason Robert Brown"), ("Songs for a New World", "Jason Robert Brown"),
    ("Jekyll & Hyde", "Frank Wildhorn"), ("The Scarlet Pimpernel", "Frank Wildhorn"),
    ("Young Frankenstein", "Mel Brooks"), ("Two Gentlemen of Verona", "Galt MacDermot"),
    ("Death Takes a Holiday", "Maury Yeston"), ("American Psycho", "Duncan Sheik"),
    # — expansion saturation round 18 (2026-06-26 run autonome) : compositeur unique « music by » (gap-filtré) —
    ("L'Opéra de quat'sous", "Kurt Weill"), ("Lady in the Dark", "Kurt Weill"),
    ("One Touch of Venus", "Kurt Weill"), ("Street Scene", "Kurt Weill"),
    ("Pal Joey", "Richard Rodgers"), ("On Your Toes", "Richard Rodgers"),
    ("The Boys from Syracuse", "Richard Rodgers"), ("Babes in Arms", "Richard Rodgers"),
    ("The Most Happy Fella", "Frank Loesser"), ("Where's Charley?", "Frank Loesser"),
    ("Do Re Mi", "Jule Styne"), ("Sugar", "Jule Styne"),
    ("Seesaw", "Cy Coleman"), ("I Love My Wife", "Cy Coleman"), ("The Life", "Cy Coleman"),
    ("Fiorello!", "Jerry Bock"), ("The Apple Tree", "Jerry Bock"), ("Tenderloin", "Jerry Bock"),
    ("Finian's Rainbow", "Burton Lane"), ("On a Clear Day You Can See Forever", "Burton Lane"),
    ("Man of La Mancha", "Mitch Leigh"),
    ("The Count of Monte Cristo", "Frank Wildhorn"), ("Bonnie & Clyde", "Frank Wildhorn"),
    ("The Full Monty", "David Yazbek"), ("Dirty Rotten Scoundrels", "David Yazbek"),
    ("Tootsie", "David Yazbek"), ("The Band's Visit", "David Yazbek"),
    ("Hairspray", "Marc Shaiman"), ("Catch Me If You Can", "Marc Shaiman"),
    ("Golden Boy", "Charles Strouse"), ("House of Flowers", "Harold Arlen"),
    # — expansion saturation round 35 (2026-06-27 run autonome, maintenance) : compositeur unique « music by » (gap-filtré) —
    ("Promises, Promises", "Burt Bacharach"), ("Subways Are for Sleeping", "Jule Styne"),
    ("Hallelujah, Baby!", "Jule Styne"), ("Knickerbocker Holiday", "Kurt Weill"), ("Love Life", "Kurt Weill"),
    ("Allegro", "Richard Rodgers"), ("Me and Juliet", "Richard Rodgers"), ("No Strings", "Richard Rodgers"),
    ("All American", "Charles Strouse"), ("Rags", "Charles Strouse"),
    ("It's a Bird...It's a Plane...It's Superman", "Charles Strouse"),
    ("Dear World", "Jerry Herman"), ("The Grand Tour", "Jerry Herman"), ("Milk and Honey", "Jerry Herman"),
    ("70, Girls, 70", "John Kander"), ("The Rink", "John Kander"), ("Steel Pier", "John Kander"),
    ("Zorba", "John Kander"), ("The Wild Party", "Andrew Lippa"), ("The Addams Family", "Andrew Lippa"),
    ("Big Fish", "Andrew Lippa"), ("A New Brain", "William Finn"), ("Falsettos", "William Finn"),
    ("The 25th Annual Putnam County Spelling Bee", "William Finn"),
    ("The Light in the Piazza", "Adam Guettel"), ("Floyd Collins", "Adam Guettel"),
    # — expansion saturation round 76 (2026-06-28 run autonome, maintenance) : compositeur unique « music by » (gap-filtré) —
    ("Blood Brothers", "Willy Russell"), ("The Hired Man", "Howard Goodall"), ("Bombay Dreams", "A. R. Rahman"),
    ("Scrooge", "Leslie Bricusse"), ("Goodbye Mr. Chips", "Leslie Bricusse"), ("Little Women", "Jason Howland"),
    ("Natasha, Pierre & The Great Comet of 1812", "Dave Malloy"), ("Preludes", "Dave Malloy"), ("Octet", "Dave Malloy"),
    ("The Beautiful Game", "Andrew Lloyd Webber"), ("By Jeeves", "Andrew Lloyd Webber"), ("Stephen Ward", "Andrew Lloyd Webber"),
    # — expansion saturation round 94 (2026-06-28 run autonome, maintenance) : compositeur unique « music by » (gap-filtré) —
    ("Lost in the Stars", "Kurt Weill"), ("Johnny Johnson", "Kurt Weill"), ("The Firebrand of Florence", "Kurt Weill"),
    ("The Golden Apple", "Jerome Moross"), ("Henry, Sweet Henry", "Bob Merrill"), ("Take Me Along", "Bob Merrill"),
    ("Greenwillow", "Frank Loesser"), ("Saturday Night", "Stephen Sondheim"), ("Road Show", "Stephen Sondheim"),
    ("Fade Out – Fade In", "Jule Styne"), ("Darling of the Day", "Jule Styne"),
    # — expansion saturation round 49 (2026-06-27 run autonome, maintenance) : compositeur unique « music by » (gap-filtré) —
    ("Kinky Boots", "Cyndi Lauper"), ("A Gentleman's Guide to Love and Murder", "Steven Lutvak"),
    ("Wonderland", "Frank Wildhorn"), ("Dracula, the Musical", "Frank Wildhorn"), ("Purlie", "Gary Geld"),
    ("Shenandoah", "Gary Geld"), ("Raisin", "Judd Woldin"), ("Soft Power", "Jeanine Tesori"),
    ("The Last Ship", "Sting"), ("Bat Out of Hell", "Jim Steinman"), ("Big River", "Roger Miller"),
    ("The Who's Tommy", "Pete Townshend"), ("Passing Strange", "Stew"),
]


# ── LIBRETTISTE (AUTEUR DU LIVRET / « book ») DE COMÉDIE MUSICALE — complète la trinité musique/paroles/
#    livret (compositeur_ + parolier_ déjà faits). DISTINCT du parolier (« lyrics ») et du compositeur. CANON
#    auteur de livret UNIQUE certain ; DUOS/ÉQUIPES ÉCARTÉS -> FAUX=0 : Guys and Dolls (Burrows+Swerling),
#    Chicago (Ebb+Fosse), The Sound of Music (Lindsay+Crouse), South Pacific (Hammerstein+Logan), The Music Man
#    (Willson+Lacey), A Chorus Line (Kirkwood+Dante), Hairspray (O'Donnell+Meehan)… ────────────────────────────
LIBRETTISTES_MUSICAL = [
    # Auteurs de livret uniques, attribution standard incontestée (« book by X »)
    ("Cabaret", "Joe Masteroff"),
    ("Fiddler on the Roof", "Joseph Stein"),
    ("Hello, Dolly!", "Michael Stewart"), ("Bye Bye Birdie", "Michael Stewart"),
    ("West Side Story", "Arthur Laurents"), ("Gypsy", "Arthur Laurents"),
    ("Funny Girl", "Isobel Lennart"),
    ("Annie", "Thomas Meehan"),
    ("Sweeney Todd", "Hugh Wheeler"), ("A Little Night Music", "Hugh Wheeler"),
    ("Company", "George Furth"),
    ("Into the Woods", "James Lapine"), ("Sunday in the Park with George", "James Lapine"),
    ("Passion", "James Lapine"),
    ("Wicked", "Winnie Holzman"),
    ("My Fair Lady", "Alan Jay Lerner"), ("Camelot", "Alan Jay Lerner"),
    ("Brigadoon", "Alan Jay Lerner"), ("Gigi", "Alan Jay Lerner"),
    ("Oklahoma!", "Oscar Hammerstein II"), ("Carousel", "Oscar Hammerstein II"),
    ("The King and I", "Oscar Hammerstein II"),
    ("Man of La Mancha", "Dale Wasserman"),
    ("Hamilton", "Lin-Manuel Miranda"), ("Rent", "Jonathan Larson"),
    ("La Cage aux Folles", "Harvey Fierstein"), ("Kinky Boots", "Harvey Fierstein"),
    ("Kiss of the Spider Woman", "Terrence McNally"), ("Ragtime", "Terrence McNally"),
    ("1776", "Peter Stone"),
    ("Pippin", "Roger O. Hirson"),
    ("Godspell", "John-Michael Tebelak"),
    ("Avenue Q", "Jeff Whitty"),
    ("Dreamgirls", "Tom Eyen"),
    # — expansion saturation round 14 (2026-06-26 run autonome) : auteur de livret UNIQUE (« book by », duos écartés) —
    ("In the Heights", "Quiara Alegría Hudes"), ("Merrily We Roll Along", "George Furth"),
    ("Anyone Can Whistle", "Arthur Laurents"), ("Spamalot", "Eric Idle"),
    ("Matilda the Musical", "Dennis Kelly"), ("Billy Elliot the Musical", "Lee Hall"),
    ("Once", "Enda Walsh"), ("The Band's Visit", "Itamar Moses"),
    ("Dear Evan Hansen", "Steven Levenson"), ("Next to Normal", "Brian Yorkey"),
    ("Beautiful: The Carole King Musical", "Douglas McGrath"), ("Memphis", "Joe DiPietro"),
    ("Spring Awakening", "Steven Sater"), ("Waitress", "Jessie Nelson"),
    ("Mean Girls", "Tina Fey"), ("Fun Home", "Lisa Kron"),
    # — expansion saturation round 45 (2026-06-27 run autonome, maintenance) : auteur de livret UNIQUE (gap-filtré) —
    ("Promises, Promises", "Neil Simon"), ("Sweet Charity", "Neil Simon"), ("Little Me", "Neil Simon"),
    ("They're Playing Our Song", "Neil Simon"), ("The Goodbye Girl", "Neil Simon"), ("The Wiz", "William F. Brown"),
    ("Carnival!", "Michael Stewart"), ("I Love My Wife", "Michael Stewart"), ("She Loves Me", "Joe Masteroff"),
    ("Zorba", "Joseph Stein"), ("The Baker's Wife", "Joseph Stein"), ("Urinetown", "Greg Kotis"),
    ("Caroline, or Change", "Tony Kushner"), ("The Full Monty", "Terrence McNally"), ("The Visit", "Terrence McNally"),
    ("A Man of No Importance", "Terrence McNally"), ("Anastasia", "Terrence McNally"),
    ("Pacific Overtures", "John Weidman"), ("Assassins", "John Weidman"), ("Contact", "John Weidman"),
    ("Road Show", "John Weidman"),
    # — expansion saturation round 63 (2026-06-27 run autonome, maintenance) : auteur de livret UNIQUE (gap-filtré) —
    ("Show Boat", "Oscar Hammerstein II"), ("Allegro", "Oscar Hammerstein II"), ("Me and Juliet", "Oscar Hammerstein II"),
    ("Carmen Jones", "Oscar Hammerstein II"), ("The Boys from Syracuse", "George Abbott"), ("Pal Joey", "John O'Hara"),
    ("Lady in the Dark", "Moss Hart"), ("Lost in the Stars", "Maxwell Anderson"), ("Knickerbocker Holiday", "Maxwell Anderson"),
    ("Street Scene", "Elmer Rice"), ("The Cradle Will Rock", "Marc Blitzstein"),
]


# ── COMPOSITEUR DE BALLET — répertoire canonique (titre FR usuel) ────────────────────────────────
BALLETS = [
    ("Le Lac des cygnes", "Piotr Ilitch Tchaïkovski"), ("Casse-Noisette", "Piotr Ilitch Tchaïkovski"),
    ("La Belle au bois dormant", "Piotr Ilitch Tchaïkovski"),
    ("Le Sacre du printemps", "Igor Stravinsky"), ("L'Oiseau de feu", "Igor Stravinsky"),
    ("Petrouchka", "Igor Stravinsky"), ("Pulcinella", "Igor Stravinsky"),
    ("Roméo et Juliette", "Sergueï Prokofiev"), ("Cendrillon", "Sergueï Prokofiev"),
    ("Giselle", "Adolphe Adam"),
    ("Coppélia", "Léo Delibes"), ("Sylvia", "Léo Delibes"),
    ("Spartacus", "Aram Khatchatourian"), ("Gayaneh", "Aram Khatchatourian"),
    ("Appalachian Spring", "Aaron Copland"), ("Rodeo", "Aaron Copland"),
    ("Daphnis et Chloé", "Maurice Ravel"), ("Boléro", "Maurice Ravel"),
    ("La Bayadère", "Ludwig Minkus"), ("Don Quichotte (ballet)", "Ludwig Minkus"),
    ("Raymonda", "Alexandre Glazounov"),
    # — expansion canon (2026-06-26) —
    ("Le Corsaire", "Adolphe Adam"),
    ("Apollon musagète", "Igor Stravinsky"),
    ("Billy the Kid", "Aaron Copland"),
    ("Le Tricorne", "Manuel de Falla"), ("Parade", "Erik Satie"),
    # — expansion 2 (2026-06-26) —
    ("Le Fils prodigue", "Sergueï Prokofiev"),
    ("Le Baiser de la fée", "Igor Stravinsky"), ("Agon", "Igor Stravinsky"),
    ("L'Amour sorcier", "Manuel de Falla"),
    # — expansion saturation (2026-06-26 loop) : ballets à compositeur unique (musique originale, arrangements écartés) —
    ("Jeux", "Claude Debussy"), ("Renard", "Igor Stravinsky"), ("Les Noces", "Igor Stravinsky"),
    ("Jeu de cartes", "Igor Stravinsky"), ("Le Loup", "Henri Dutilleux"),
    ("Les Animaux modèles", "Francis Poulenc"), ("Les Biches", "Francis Poulenc"),
    ("Le Mandarin merveilleux", "Béla Bartók"), ("Checkmate", "Arthur Bliss"), ("Façade", "William Walton"),
    ("La Création du monde", "Darius Milhaud"), ("Le Bœuf sur le toit", "Darius Milhaud"),
    ("Le Train bleu", "Darius Milhaud"), ("Le Pavillon d'Armide", "Nikolaï Tcherepnine"),
    # — expansion saturation round 5 (2026-06-26 loop) : ballets à compositeur unique (musique originale) —
    ("La Valse", "Maurice Ravel"), ("Ma mère l'Oye", "Maurice Ravel"),
    ("Ondine", "Hans Werner Henze"), ("The Prince of the Pagodas", "Benjamin Britten"),
    ("Anna Karénine", "Rodion Chtchedrine"),
    # — expansion saturation round 6 (2026-06-26 run autonome) : ballets à compositeur unique (musique originale) —
    ("Orpheus", "Igor Stravinsky"), ("Scènes de ballet", "Igor Stravinsky"),
    ("Le Pas d'acier", "Sergueï Prokofiev"), ("La Fleur de pierre", "Sergueï Prokofiev"),
    ("Les Saisons", "Alexandre Glazounov"),
    ("Le Prince de bois", "Béla Bartók"),
    ("L'Âge d'or", "Dmitri Chostakovitch"), ("Le Boulon", "Dmitri Chostakovitch"),
    ("Le Ruisseau limpide", "Dmitri Chostakovitch"),
    ("Le Pavot rouge", "Reinhold Glière"), ("Le Cavalier de bronze", "Reinhold Glière"),
    ("Les Flammes de Paris", "Boris Assafiev"), ("La Fontaine de Bakhtchissaraï", "Boris Assafiev"),
    ("Nobilissima Visione", "Paul Hindemith"), ("Les Quatre Tempéraments", "Paul Hindemith"),
    ("Maratona di danza", "Hans Werner Henze"),
    # — expansion saturation round 34 (2026-06-27 run autonome, maintenance) : compositeur unique, musique originale (gap-filtré) —
    ("Sur le Borysthène", "Sergueï Prokofiev"), ("Chout", "Sergueï Prokofiev"),
    ("Danses concertantes", "Igor Stravinsky"), ("La Péri", "Paul Dukas"),
    ("Le Festin de l'araignée", "Albert Roussel"), ("Bacchus et Ariane", "Albert Roussel"),
    ("Namouna", "Édouard Lalo"), ("Les Deux Pigeons", "André Messager"),
    ("Cydalise et le Chèvre-pied", "Gabriel Pierné"), ("Istar", "Vincent d'Indy"),
    ("Fall River Legend", "Morton Gould"), ("Interplay", "Morton Gould"),
    ("Fancy Free", "Leonard Bernstein"), ("Undertow", "William Schuman"),
    ("Le Diable à quatre", "Adolphe Adam"),
    # — expansion saturation round 97 (2026-06-28 run autonome, maintenance) : compositeur unique, musique originale (gap-filtré) —
    ("La Mouette", "Rodion Chtchedrine"), ("Les Forains", "Henri Sauguet"), ("La Chatte", "Henri Sauguet"),
    ("Le Bal", "Vittorio Rieti"), ("Barabau", "Vittorio Rieti"), ("Ode", "Nicolas Nabokov"),
    ("Still Life at the Penguin Café", "Simon Jeffes"), ("Hobson's Choice", "Paul Reade"), ("Edward II (ballet)", "John McCabe"),
    ("Alice's Adventures in Wonderland (ballet)", "Joby Talbot"), ("The Winter's Tale (ballet)", "Joby Talbot"),
    # — expansion saturation round 51 (2026-06-27 run autonome, maintenance) : compositeur unique, musique originale (gap-filtré) —
    ("Le Chant du rossignol", "Igor Stravinsky"), ("Perséphone", "Igor Stravinsky"),
    ("Don Quichotte (Nabokov)", "Nicolas Nabokov"), ("Le Dieu bleu", "Reynaldo Hahn"),
    ("La Tragédie de Salomé", "Florent Schmitt"), ("Impressions de music-hall", "Gabriel Pierné"),
    ("Khamma", "Claude Debussy"), ("La Boîte à joujoux", "Claude Debussy"), ("Salade", "Darius Milhaud"),
    ("Les Fâcheux", "Georges Auric"), ("Les Matelots", "Georges Auric"), ("Phèdre (ballet)", "Georges Auric"),
]

# ── LIBRETTISTE D'OPÉRA — UNIQUEMENT les opéras à librettiste UNIQUE certain (duos Illica+Giacosa
#    de Puccini ÉCARTÉS : multi-valeur, FAUX=0) ────────────────────────────────────────────────────
LIBRETTISTES_OPERA = [
    ("Le nozze di Figaro", "Lorenzo Da Ponte"), ("Don Giovanni", "Lorenzo Da Ponte"),
    ("Così fan tutte", "Lorenzo Da Ponte"),
    ("Otello", "Arrigo Boito"), ("Falstaff", "Arrigo Boito"),
    ("Rigoletto", "Francesco Maria Piave"), ("La traviata", "Francesco Maria Piave"),
    ("Il barbiere di Siviglia", "Cesare Sterbini"),
    ("Lucia di Lammermoor", "Salvadore Cammarano"),
    ("L'elisir d'amore", "Felice Romani"), ("Norma", "Felice Romani"),
    ("La sonnambula", "Felice Romani"),
    ("Der Rosenkavalier", "Hugo von Hofmannsthal"), ("Elektra", "Hugo von Hofmannsthal"),
    ("Ariadne auf Naxos", "Hugo von Hofmannsthal"),
    # — expansion saturation round 2 (2026-06-26 loop) : librettiste unique certain —
    ("Ernani", "Francesco Maria Piave"), ("I due Foscari", "Francesco Maria Piave"),
    ("La forza del destino", "Francesco Maria Piave"), ("Stiffelio", "Francesco Maria Piave"),
    ("Il corsaro", "Francesco Maria Piave"),
    ("Il pirata", "Felice Romani"), ("Lucrezia Borgia", "Felice Romani"), ("Anna Bolena", "Felice Romani"),
    ("Beatrice di Tenda", "Felice Romani"), ("I Capuleti e i Montecchi", "Felice Romani"),
    ("Luisa Miller", "Salvadore Cammarano"), ("Roberto Devereux", "Salvadore Cammarano"),
    ("La Gioconda", "Arrigo Boito"), ("Mefistofele", "Arrigo Boito"),
    ("Die Frau ohne Schatten", "Hugo von Hofmannsthal"), ("Arabella", "Hugo von Hofmannsthal"),
    ("Orfeo ed Euridice", "Ranieri de' Calzabigi"),
    # — expansion saturation round 14 (2026-06-26 run autonome) : librettiste UNIQUE certain (auto-librettistes inclus) —
    ("Andrea Chénier", "Luigi Illica"),
    ("Fedora", "Arturo Colautti"), ("Adriana Lecouvreur", "Arturo Colautti"),
    ("Les Contes d'Hoffmann", "Jules Barbier"), ("Pelléas et Mélisande", "Maurice Maeterlinck"),
    ("Boris Godounov", "Modeste Moussorgski"), ("Khovanshchina", "Modeste Moussorgski"),
    ("Lohengrin", "Richard Wagner"), ("Tannhäuser", "Richard Wagner"),
    ("Tristan und Isolde", "Richard Wagner"), ("Parsifal", "Richard Wagner"),
    ("Der fliegende Holländer", "Richard Wagner"), ("Die Meistersinger von Nürnberg", "Richard Wagner"),
    ("Nabucco", "Temistocle Solera"), ("La Cenerentola", "Jacopo Ferretti"),
    ("Semiramide", "Gaetano Rossi"), ("Tancredi", "Gaetano Rossi"),
    ("Wozzeck", "Alban Berg"), ("Lulu", "Alban Berg"),
    ("La Dame de pique", "Modest Tchaïkovski"),
    # — expansion saturation round 44 (2026-06-27 run autonome, maintenance) : librettiste UNIQUE certain (gap-filtré) —
    ("Hänsel und Gretel", "Adelheid Wette"), ("Pagliacci", "Ruggero Leoncavallo"),
    ("Samson et Dalila", "Ferdinand Lemaire"), ("Thaïs", "Louis Gallet"),
    ("Cendrillon (Massenet)", "Henri Cain"), ("Don Quichotte (Massenet)", "Henri Cain"),
    ("La Wally", "Luigi Illica"), ("Iris", "Luigi Illica"),
    # — expansion saturation round 64 (2026-06-27 run autonome, maintenance) : librettiste UNIQUE (auto-librettistes inclus ; gap-filtré) —
    ("Die Zauberflöte", "Emanuel Schikaneder"), ("Der Freischütz", "Friedrich Kind"), ("Les Troyens", "Hector Berlioz"),
    ("Béatrice et Bénédict", "Hector Berlioz"), ("Mireille", "Michel Carré"), ("Louise", "Gustave Charpentier"),
    ("Pénélope", "René Fauchois"), ("Ariane et Barbe-Bleue", "Maurice Maeterlinck"), ("L'Enfant et les sortilèges", "Colette"),
    ("Dialogues des carmélites", "Georges Bernanos"), ("La Voix humaine", "Jean Cocteau"), ("Les Mamelles de Tirésias", "Guillaume Apollinaire"),
    ("Intermezzo", "Richard Strauss"), ("Palestrina", "Hans Pfitzner"), ("Cardillac", "Ferdinand Lion"),
    ("Mathis der Maler", "Paul Hindemith"), ("Doktor Faust", "Ferruccio Busoni"),
]


# ── PAROLIER DE COMÉDIE MUSICALE — parolier UNIQUE certain (« lyrics by ») ───────────────────────
PAROLIERS_MUSICAL = [
    ("Jesus Christ Superstar", "Tim Rice"), ("Evita", "Tim Rice"),
    ("Cats", "T. S. Eliot"),
    ("Hamilton", "Lin-Manuel Miranda"), ("In the Heights", "Lin-Manuel Miranda"),
    ("Little Shop of Horrors", "Howard Ashman"),
    # Oscar Hammerstein II (paroles des Rodgers & Hammerstein)
    ("Oklahoma!", "Oscar Hammerstein II"), ("Carousel", "Oscar Hammerstein II"),
    ("South Pacific", "Oscar Hammerstein II"), ("The King and I", "Oscar Hammerstein II"),
    ("The Sound of Music", "Oscar Hammerstein II"),
    # Stephen Sondheim parolier (y compris les œuvres où il n'est QUE parolier)
    ("West Side Story", "Stephen Sondheim"), ("Gypsy", "Stephen Sondheim"),
    ("Sweeney Todd", "Stephen Sondheim"), ("Into the Woods", "Stephen Sondheim"),
    ("Company", "Stephen Sondheim"), ("A Little Night Music", "Stephen Sondheim"),
    ("Follies", "Stephen Sondheim"), ("Assassins", "Stephen Sondheim"),
    # Stephen Schwartz / Jerry Herman / Frank Loesser (music & lyrics = parolier = compositeur)
    ("Wicked", "Stephen Schwartz"), ("Godspell", "Stephen Schwartz"), ("Pippin", "Stephen Schwartz"),
    ("Hello, Dolly!", "Jerry Herman"), ("Mame", "Jerry Herman"), ("La Cage aux Folles", "Jerry Herman"),
    ("Guys and Dolls", "Frank Loesser"),
    ("How to Succeed in Business Without Really Trying", "Frank Loesser"),
    ("The Music Man", "Meredith Willson"), ("Rent", "Jonathan Larson"),
    # Fred Ebb (Kander & Ebb) / Martin Charnin / Sheldon Harnick / Bob Merrill
    ("Cabaret", "Fred Ebb"), ("Chicago", "Fred Ebb"),
    ("Annie", "Martin Charnin"), ("Fiddler on the Roof", "Sheldon Harnick"),
    ("Funny Girl", "Bob Merrill"),
    # — expansion saturation round 2 (2026-06-26 loop) : parolier unique certain (titres ambigus qualifiés) —
    ("Chess", "Tim Rice"), ("Aida (comédie musicale)", "Tim Rice"),
    ("Ragtime", "Lynn Ahrens"), ("Once on This Island", "Lynn Ahrens"),
    ("Seussical", "Lynn Ahrens"), ("Anastasia", "Lynn Ahrens"),
    ("The Prince of Egypt", "Stephen Schwartz"), ("City of Angels", "David Zippel"),
    ("Do I Hear a Waltz?", "Stephen Sondheim"), ("Tell Me on a Sunday", "Don Black"),
    # — expansion saturation round 14 (2026-06-26 run autonome) : parolier UNIQUE (« lyrics by », duos écartés) —
    ("The Little Mermaid", "Howard Ashman"), ("Dreamgirls", "Tom Eyen"),
    ("Matilda the Musical", "Tim Minchin"), ("Groundhog Day", "Tim Minchin"),
    ("Hadestown", "Anaïs Mitchell"), ("Spring Awakening", "Steven Sater"),
    ("Next to Normal", "Brian Yorkey"), ("Fun Home", "Lisa Kron"),
    ("Waitress", "Sara Bareilles"), ("Oliver!", "Lionel Bart"),
    ("Joseph and the Amazing Technicolor Dreamcoat", "Tim Rice"),
    ("Whistle Down the Wind", "Jim Steinman"),
    ("Kiss of the Spider Woman", "Fred Ebb"), ("The Scottsboro Boys", "Fred Ebb"),
    ("Curtains", "Fred Ebb"), ("Mack and Mabel", "Jerry Herman"),
    ("Half a Sixpence", "David Heneker"),
    # — expansion saturation round 44 (2026-06-27 run autonome, maintenance) : parolier UNIQUE « lyrics by » (gap-filtré) —
    ("From Here to Eternity", "Tim Rice"), ("She Loves Me", "Sheldon Harnick"), ("Fiorello!", "Sheldon Harnick"),
    ("The Apple Tree", "Sheldon Harnick"), ("Woman of the Year", "Fred Ebb"), ("A Man of No Importance", "Lynn Ahrens"),
    ("Sweet Charity", "Dorothy Fields"), ("Seesaw", "Dorothy Fields"), ("Redhead", "Dorothy Fields"),
    ("Bye Bye Birdie", "Lee Adams"), ("Applause", "Lee Adams"), ("Golden Boy", "Lee Adams"),
    ("Promises, Promises", "Hal David"), ("The Fantasticks", "Tom Jones"), ("110 in the Shade", "Tom Jones"),
    ("I Do! I Do!", "Tom Jones"), ("A Chorus Line", "Edward Kleban"), ("Little Me", "Carolyn Leigh"),
    # — expansion saturation round 62 (2026-06-27 run autonome, maintenance) : parolier UNIQUE fondateur (gap-filtré) —
    ("Camelot", "Alan Jay Lerner"), ("My Fair Lady", "Alan Jay Lerner"), ("Brigadoon", "Alan Jay Lerner"),
    ("Gigi", "Alan Jay Lerner"), ("Paint Your Wagon", "Alan Jay Lerner"), ("Finian's Rainbow", "E.Y. Harburg"),
    ("Jamaica", "E.Y. Harburg"), ("Lady in the Dark", "Ira Gershwin"), ("Of Thee I Sing", "Ira Gershwin"),
    ("Funny Face", "Ira Gershwin"), ("Kiss Me, Kate", "Cole Porter"), ("Anything Goes", "Cole Porter"),
    ("Can-Can", "Cole Porter"), ("Annie Get Your Gun", "Irving Berlin"), ("Call Me Madam", "Irving Berlin"),
    ("Show Boat", "Oscar Hammerstein II"),
]


# ── AUTEUR DE JEU DE SOCIÉTÉ — Wikidata FR ultra-sparse (16 ent.) ; CANON designer unique certain.
#    Duos (Trivial Pursuit, 7 Wonders Duel, El Grande, Loups-Garous…) ÉCARTÉS. ─────────────────────
JEUX_SOCIETE = [
    ("Les Colons de Catane", "Klaus Teuber"), ("Carcassonne", "Klaus-Jürgen Wrede"),
    ("Les Aventuriers du Rail", "Alan R. Moon"), ("Pandémie", "Matt Leacock"),
    ("7 Wonders", "Antoine Bauza"), ("Dominion", "Donald X. Vaccarino"),
    ("Agricola", "Uwe Rosenberg"), ("Caverna", "Uwe Rosenberg"),
    ("Puerto Rico", "Andreas Seyfarth"), ("Azul", "Michael Kiesling"),
    ("Les Châteaux de Bourgogne", "Stefan Feld"), ("Terraforming Mars", "Jacob Fryxelius"),
    ("Wingspan", "Elizabeth Hargrave"), ("Scythe", "Jamey Stegmaier"),
    ("Splendor", "Marc André"), ("Dixit", "Jean-Louis Roubira"),
    ("Citadelles", "Bruno Faidutti"), ("Diplomatie", "Allan B. Calhamer"),
    ("Through the Ages", "Vlaada Chvátil"), ("Codenames", "Vlaada Chvátil"),
    ("Galaxy Trucker", "Vlaada Chvátil"), ("Small World", "Philippe Keyaerts"),
    ("King of Tokyo", "Richard Garfield"), ("Magic : L'Assemblée", "Richard Garfield"),
    ("Concordia", "Mac Gerdts"), ("Power Grid", "Friedemann Friese"),
    ("Brass", "Martin Wallace"), ("Cluedo", "Anthony E. Pratt"),
    ("Risk", "Albert Lamorisse"),
    # — expansion canon (2026-06-26) : designers uniques certains —
    ("Le Havre", "Uwe Rosenberg"), ("Bohnanza", "Uwe Rosenberg"), ("Patchwork", "Uwe Rosenberg"),
    ("Tigre & Euphrate", "Reiner Knizia"), ("Ra", "Reiner Knizia"), ("Samouraï", "Reiner Knizia"),
    ("Hanabi", "Antoine Bauza"), ("Takenoko", "Antoine Bauza"), ("Tokaido", "Antoine Bauza"),
    ("Five Tribes", "Bruno Cathala"), ("Kingdomino", "Bruno Cathala"),
    ("Trajan", "Stefan Feld"), ("Notre Dame", "Stefan Feld"),
    ("Forbidden Island", "Matt Leacock"),
    ("Blood Rage", "Eric Lang"), ("Gloomhaven", "Isaac Childres"),
    ("Age of Steam", "Martin Wallace"),
    # — expansion 2 (2026-06-26) : designers uniques certains (Wikidata FR très faible sur ce domaine) —
    ("Lost Cities", "Reiner Knizia"), ("Modern Art", "Reiner Knizia"), ("Battle Line", "Reiner Knizia"),
    ("A Feast for Odin", "Uwe Rosenberg"), ("Ora et Labora", "Uwe Rosenberg"), ("Glass Road", "Uwe Rosenberg"),
    ("Bora Bora", "Stefan Feld"), ("Bruges", "Stefan Feld"),
    ("Mage Knight", "Vlaada Chvátil"),
    ("London", "Martin Wallace"), ("Steam", "Martin Wallace"),
    ("Kingdom Builder", "Donald X. Vaccarino"),
    ("The Gallerist", "Vital Lacerda"), ("Lisboa", "Vital Lacerda"), ("On Mars", "Vital Lacerda"),
    ("Robinson Crusoé", "Ignacy Trzewiczek"),
    ("Sushi Go!", "Phil Walker-Harding"), ("Bärenpark", "Phil Walker-Harding"),
    ("Great Western Trail", "Alexander Pfister"), ("Maracaibo", "Alexander Pfister"),
    ("The Mind", "Wolfgang Warsch"), ("Les Charlatans de Belcastel", "Wolfgang Warsch"),
    ("Tapestry", "Jamey Stegmaier"), ("Charterstone", "Jamey Stegmaier"),
    ("RoboRally", "Richard Garfield"),
    ("Forbidden Desert", "Matt Leacock"),
    ("Rising Sun", "Eric Lang"), ("Eclipse", "Touko Tahkokallio"),
    ("Underwater Cities", "Vladimír Suchý"), ("Manhattan", "Andreas Seyfarth"),
    ("For Sale", "Stefan Dorra"), ("Mascarade", "Bruno Faidutti"),
    ("Battlestar Galactica", "Corey Konieczka"),
    # — expansion saturation (2026-06-26 loop) : designers uniques certains —
    ("Amun-Re", "Reiner Knizia"), ("Through the Desert", "Reiner Knizia"),
    ("Schotten Totten", "Reiner Knizia"), ("Keltis", "Reiner Knizia"), ("Ingenious", "Reiner Knizia"),
    ("Nusfjord", "Uwe Rosenberg"), ("Reykholt", "Uwe Rosenberg"), ("Hallertau", "Uwe Rosenberg"),
    ("At the Gates of Loyang", "Uwe Rosenberg"),
    ("Luna", "Stefan Feld"), ("AquaSphere", "Stefan Feld"), ("Amerigo", "Stefan Feld"),
    ("The Oracle of Delphi", "Stefan Feld"),
    ("Tinners' Trail", "Martin Wallace"), ("Automobile", "Martin Wallace"),
    ("A Few Acres of Snow", "Martin Wallace"),
    ("Vinhos", "Vital Lacerda"), ("CO₂", "Vital Lacerda"), ("Kanban EV", "Vital Lacerda"),
    ("Mombasa", "Alexander Pfister"), ("Boonlake", "Alexander Pfister"),
    ("Blackout: Hong Kong", "Alexander Pfister"),
    ("Space Alert", "Vlaada Chvátil"), ("Dungeon Lords", "Vlaada Chvátil"), ("Dungeon Petz", "Vlaada Chvátil"),
    ("Ghost Stories", "Antoine Bauza"), ("Samurai Spirit", "Antoine Bauza"),
    ("Nefarious", "Donald X. Vaccarino"), ("Entdecker", "Klaus Teuber"),
    # — expansion saturation round 3 (2026-06-26 loop) : catalogues profonds, designers uniques —
    ("Taj Mahal", "Reiner Knizia"), ("Medici", "Reiner Knizia"), ("High Society", "Reiner Knizia"),
    ("Blue Moon", "Reiner Knizia"), ("The Quest for El Dorado", "Reiner Knizia"),
    ("Yellow & Yangtze", "Reiner Knizia"), ("Babylonia", "Reiner Knizia"), ("L.L.A.M.A.", "Reiner Knizia"),
    ("Blue Lagoon", "Reiner Knizia"), ("Stephenson's Rocket", "Reiner Knizia"),
    ("Cottage Garden", "Uwe Rosenberg"), ("Spring Meadow", "Uwe Rosenberg"), ("Indian Summer", "Uwe Rosenberg"),
    ("In the Year of the Dragon", "Stefan Feld"), ("Macao", "Stefan Feld"), ("Rialto", "Stefan Feld"),
    ("Carpe Diem", "Stefan Feld"), ("Hamburgum", "Stefan Feld"), ("Bonfire", "Stefan Feld"),
    ("Anno 1800", "Martin Wallace"),
    ("Weather Machine", "Vital Lacerda"), ("Escape Plan", "Vital Lacerda"),
    ("Oh My Goods!", "Alexander Pfister"), ("Port Royal", "Alexander Pfister"),
    ("Pictomania", "Vlaada Chvátil"), ("Tash-Kalar", "Vlaada Chvátil"),
    ("Last Bastion", "Antoine Bauza"), ("Queendomino", "Bruno Cathala"),
    ("Netrunner", "Richard Garfield"), ("Bunny Kingdom", "Richard Garfield"), ("KeyForge", "Richard Garfield"),
    ("Barbarossa", "Klaus Teuber"),
    # — expansion saturation round 23 (2026-06-26 run autonome, maintenance) : designer unique (gap-filtré) —
    ("My City", "Reiner Knizia"), ("Whale Riders", "Reiner Knizia"),
    ("Mamma Mia!", "Uwe Rosenberg"), ("New York Zoo", "Uwe Rosenberg"),
    ("Castles of Tuscany", "Stefan Feld"), ("Marrakesh", "Stefan Feld"), ("Forum Trajanum", "Stefan Feld"),
    ("Expedition to Newdale", "Alexander Pfister"),
    # — expansion saturation round 33 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Cascadia", "Randy Flynn"), ("Calico", "Kevin Russ"), ("The Crew", "Thomas Sing"),
    ("Cartographers", "Jordy Adan"), ("Roll Player", "Keith Matejka"), ("Everdell", "James A. Wilson"),
    ("Spirit Island", "R. Eric Reuss"), ("Frosthaven", "Isaac Childres"), ("Aeon's End", "Kevin Riley"),
    ("Clank!", "Paul Dennen"), ("Dune: Imperium", "Paul Dennen"), ("Res Arcana", "Tom Lehmann"),
    ("Race for the Galaxy", "Tom Lehmann"), ("Ark Nova", "Mathias Wigge"), ("Liberté", "Martin Wallace"),
    ("Struggle of Empires", "Martin Wallace"), ("Tutankhamen", "Reiner Knizia"), ("Circus Flohcati", "Reiner Knizia"),
    # — expansion saturation round 40 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Praga Caput Regni", "Vladimír Suchý"), ("Pulsar 2849", "Vladimír Suchý"), ("Brass: Lancashire", "Martin Wallace"),
    ("Navegador", "Mac Gerdts"), ("Imperial", "Mac Gerdts"), ("Antike", "Mac Gerdts"),
    ("Watergate", "Matthias Cramer"), ("Lancaster", "Matthias Cramer"), ("Glen More", "Matthias Cramer"),
    ("Hansa Teutonica", "Andreas Steding"), ("Yokohama", "Hisashi Hayashi"), ("Trains", "Hisashi Hayashi"),
    ("Inis", "Christian Martinez"), ("Inventions", "Vital Lacerda"), ("Keydom", "Richard Breese"),
    # — expansion saturation round 50 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("6 nimmt!", "Wolfgang Kramer"), ("Alhambra", "Dirk Henn"), ("Shogun (Dirk Henn)", "Dirk Henn"),
    ("Wallenstein", "Dirk Henn"), ("Friday", "Friedemann Friese"), ("Fauna", "Friedemann Friese"),
    ("504", "Friedemann Friese"), ("Targi", "Andreas Steiner"), ("Hive", "John Yianni"),
    ("Santorini", "Gordon Hamilton"), ("Welcome To...", "Benoit Turpin"), ("It's a Wonderful World", "Frédéric Guérard"),
    ("Imhotep", "Phil Walker-Harding"), ("Gizmos", "Phil Walker-Harding"), ("Razzia!", "Reiner Knizia"),
    ("Palazzo", "Reiner Knizia"), ("En Garde", "Reiner Knizia"), ("Löwenherz", "Klaus Teuber"),
    # — expansion saturation round 58 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Auf Achse", "Wolfgang Kramer"), ("Heimlich & Co.", "Wolfgang Kramer"), ("Midnight Party", "Wolfgang Kramer"),
    ("Colt Express", "Christophe Raimbault"), ("Flamme Rouge", "Asger Harding Granerud"), ("Photosynthesis", "Hjalmar Hach"),
    ("Karuba", "Rüdiger Dorn"), ("Las Vegas", "Rüdiger Dorn"), ("Istanbul", "Rüdiger Dorn"), ("Goa", "Rüdiger Dorn"),
    ("Jambo", "Rüdiger Dorn"), ("Camel Up", "Steffen Bogen"), ("Skull", "Hervé Marly"),
    ("Decrypto", "Thomas Dagenais-Lespérance"), ("Ganz schön clever", "Wolfgang Warsch"), ("Reef", "Emerson Matsuuchi"),
    ("Century: Spice Road", "Emerson Matsuuchi"), ("Raiders of the North Sea", "Shem Phillips"),
    # — expansion saturation round 77 (2026-06-28 run autonome, maintenance) : classiques à designer unique (gap-filtré) —
    ("Tichu", "Urs Hostettler"), ("Set", "Marsha Falco"), ("Blokus", "Bernard Tavitian"), ("Qwirkle", "Susan McKinley Ross"),
    ("Rummikub", "Ephraim Hertzano"), ("Othello", "Goro Hasegawa"), ("Mastermind", "Mordecai Meirowitz"), ("Boggle", "Allan Turoff"),
    ("Scrabble", "Alfred Mosher Butts"), ("Pictionary", "Robert Angel"), ("Taboo", "Brian Hersch"), ("Saboteur", "Frederic Moyersoen"),
    ("Bang!", "Emiliano Sciarra"), ("Coup", "Rikki Tahta"), ("The Resistance", "Don Eskridge"), ("Love Letter", "Seiji Kanai"),
    # — expansion saturation round 91 (2026-06-28 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Barony", "Marc André"), ("7 Wonders Architects", "Antoine Bauza"), ("Coloretto", "Michael Schacht"),
    ("Zooloretto", "Michael Schacht"), ("Web of Power", "Michael Schacht"), ("Hansa", "Michael Schacht"),
    ("Augustus", "Paolo Mori"), ("Libertalia", "Paolo Mori"), ("Ethnos", "Paolo Mori"), ("Blitzkrieg!", "Paolo Mori"),
    ("Cacao", "Phil Walker-Harding"), ("Silver & Gold", "Phil Walker-Harding"), ("Cat Lady", "Josh Wood"), ("Trekking the National Parks", "Charlie Bink"),
    # — expansion saturation round 99 (2026-06-28 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Risk Legacy", "Rob Daviau"), ("SeaFall", "Rob Daviau"), ("A Game of Thrones: The Board Game", "Christian T. Petersen"),
    ("Twilight Imperium", "Christian T. Petersen"), ("Acquire", "Sid Sackson"), ("Bazaar", "Sid Sackson"), ("Can't Stop", "Sid Sackson"),
    ("I'm the Boss!", "Sid Sackson"), ("Munchkin", "Steve Jackson"), ("Illuminati", "Steve Jackson"), ("Car Wars", "Steve Jackson"),
    ("Ogre", "Steve Jackson"), ("Wiz-War", "Tom Jolly"), ("Tsuro", "Tom McMurchie"), ("Sleeping Queens", "Miranda Evarts"),
]


# ── CRÉATEUR DE POLICE D'ÉCRITURE (type designer) — Wikidata FR ultra-sparse (Q17489160 = 0 entité au
#    2026-06-26). CANON designer UNIQUE certain ; CO-CRÉATIONS ÉCARTÉES (Helvetica=Miedinger+Hoffmann,
#    Times New Roman=Morison+Lardent, Myriad/Lucida/Archer = duos) -> FAUX=0. ────────────────────────────
POLICES = [
    # Historiques (caractères éponymes, attribution canonique indiscutable)
    ("Garamond", "Claude Garamond"), ("Caslon", "William Caslon"),
    ("Baskerville", "John Baskerville"), ("Bodoni", "Giambattista Bodoni"),
    # Paul Renner / Eric Gill
    ("Futura", "Paul Renner"),
    ("Gill Sans", "Eric Gill"), ("Perpetua", "Eric Gill"), ("Joanna", "Eric Gill"),
    # Adrian Frutiger
    ("Univers", "Adrian Frutiger"), ("Frutiger", "Adrian Frutiger"), ("Avenir", "Adrian Frutiger"),
    # Hermann Zapf
    ("Optima", "Hermann Zapf"), ("Palatino", "Hermann Zapf"), ("Zapfino", "Hermann Zapf"),
    ("Melior", "Hermann Zapf"), ("Aldus", "Hermann Zapf"),
    # Matthew Carter
    ("Verdana", "Matthew Carter"), ("Georgia", "Matthew Carter"), ("Tahoma", "Matthew Carter"),
    ("Snell Roundhand", "Matthew Carter"), ("Galliard", "Matthew Carter"),
    # Lucas de Groot
    ("Calibri", "Lucas de Groot"), ("Consolas", "Lucas de Groot"),
    # Adobe : Carol Twombly / Robert Slimbach
    ("Trajan", "Carol Twombly"),
    ("Minion", "Robert Slimbach"), ("Adobe Garamond", "Robert Slimbach"),
    # Howard Kettler / Oswald Cooper
    ("Courier", "Howard Kettler"), ("Cooper Black", "Oswald Bruce Cooper"),
    # Erik Spiekermann
    ("FF Meta", "Erik Spiekermann"), ("Fira Sans", "Erik Spiekermann"), ("ITC Officina", "Erik Spiekermann"),
    # Tschichold / Cassandre / Excoffon / Wolpe
    ("Sabon", "Jan Tschichold"), ("Peignot", "A. M. Cassandre"),
    ("Mistral", "Roger Excoffon"), ("Antique Olive", "Roger Excoffon"), ("Banco", "Roger Excoffon"),
    ("Albertus", "Berthold Wolpe"),
    # Frederic Goudy / Morris Fuller Benton
    ("Goudy Old Style", "Frederic Goudy"), ("Copperplate Gothic", "Frederic Goudy"),
    ("Kennerley", "Frederic Goudy"),
    ("Franklin Gothic", "Morris Fuller Benton"), ("News Gothic", "Morris Fuller Benton"),
    ("Souvenir", "Morris Fuller Benton"),
    # Tobias Frere-Jones / Jonathan Hoefler (mono seulement)
    ("Gotham", "Tobias Frere-Jones"), ("Interstate", "Tobias Frere-Jones"), ("Whitney", "Tobias Frere-Jones"),
    ("Hoefler Text", "Jonathan Hoefler"),
    # Néerlandais : Martin Majoor / Bram de Does
    ("FF Scala", "Martin Majoor"), ("FF Quadraat", "Martin Majoor"),
    ("Trinité", "Bram de Does"), ("Lexicon", "Bram de Does"),
    # Divers mono certains
    ("Comic Sans", "Vincent Connare"), ("Proxima Nova", "Mark Simonson"),
    ("Memphis", "Rudolf Wolf"), ("Centaur", "Bruce Rogers"), ("Dax", "Hans Reichel"),
    # — expansion saturation (2026-06-26 loop) : type designers uniques, co-créations écartées —
    ("ITC Avant Garde Gothic", "Herb Lubalin"), ("ITC Lubalin Graph", "Herb Lubalin"),
    ("Bell Centennial", "Matthew Carter"), ("Bell Gothic", "Chauncey H. Griffith"),
    ("Cheltenham", "Bertram Goodhue"),
    ("Hobo", "Morris Fuller Benton"), ("Broadway", "Morris Fuller Benton"),
    ("Bank Gothic", "Morris Fuller Benton"),
    ("Cronos", "Robert Slimbach"), ("Warnock", "Robert Slimbach"), ("Caflisch Script", "Robert Slimbach"),
    ("Chaparral", "Carol Twombly"), ("Lithos", "Carol Twombly"), ("Charlemagne", "Carol Twombly"),
    ("Mrs Eaves", "Zuzana Licko"), ("Filosofia", "Zuzana Licko"),
    ("Choc", "Roger Excoffon"), ("Calypso", "Roger Excoffon"),
    ("Bifur", "A. M. Cassandre"),
    ("Pegasus", "Berthold Wolpe"),
    ("Zapf Chancery", "Hermann Zapf"), ("Zapf Dingbats", "Hermann Zapf"),
    # — expansion saturation round 4 (2026-06-26 loop) : type designers uniques (duos/multi écartés) —
    ("OCR-B", "Adrian Frutiger"), ("Serifa", "Adrian Frutiger"), ("Glypha", "Adrian Frutiger"),
    ("Vectora", "Adrian Frutiger"), ("Centennial", "Adrian Frutiger"),
    ("ITC Charter", "Matthew Carter"), ("Olympian", "Matthew Carter"),
    ("Utopia", "Robert Slimbach"), ("Kepler", "Robert Slimbach"), ("Brioso", "Robert Slimbach"),
    ("Garamond Premier", "Robert Slimbach"),
    ("Goudy Sans", "Frederic Goudy"), ("Berkeley Old Style", "Frederic Goudy"),
    ("Century Schoolbook", "Morris Fuller Benton"), ("Stymie", "Morris Fuller Benton"),
    ("Le Monde Journal", "Jean François Porchez"), ("Ambroise", "Jean François Porchez"),
    ("Swift", "Gerard Unger"), ("Gulliver", "Gerard Unger"), ("Coranto", "Gerard Unger"),
    ("Vesta", "Gerard Unger"),
    ("Graphik", "Christian Schwartz"), ("Amplitude", "Christian Schwartz"),
    ("Stone Sans", "Sumner Stone"), ("Fedra", "Peter Bil'ak"), ("History", "Peter Bil'ak"),
    # — expansion saturation round 9 (2026-06-26 run autonome) : type designers UNIQUES (co-créations écartées) —
    ("Apollo", "Adrian Frutiger"), ("Méridien", "Adrian Frutiger"), ("Egyptienne F", "Adrian Frutiger"),
    ("Versailles", "Adrian Frutiger"),
    ("Comenius", "Hermann Zapf"), ("Marconi", "Hermann Zapf"), ("Medici Script", "Hermann Zapf"),
    ("Miller", "Matthew Carter"), ("Mantinia", "Matthew Carter"), ("Skia", "Matthew Carter"),
    ("Poetica", "Robert Slimbach"), ("Sanvito", "Robert Slimbach"), ("Arno", "Robert Slimbach"),
    ("Nueva", "Carol Twombly"), ("Viva", "Carol Twombly"),
    ("Clearface", "Morris Fuller Benton"), ("Agency Gothic", "Morris Fuller Benton"),
    ("Century Old Style", "Morris Fuller Benton"),
    ("Deepdene", "Frederic Goudy"), ("Italian Old Style", "Frederic Goudy"),
    ("Demos", "Gerard Unger"), ("Praxis", "Gerard Unger"), ("Capitolium", "Gerard Unger"),
    ("Matrix", "Zuzana Licko"), ("Triplex", "Zuzana Licko"),
    ("Parisine", "Jean François Porchez"), ("Anisette", "Jean François Porchez"),
    ("Greta", "Peter Bil'ak"), ("Lava", "Peter Bil'ak"),
    ("Stone Serif", "Sumner Stone"), ("Trebuchet MS", "Vincent Connare"),
    ("Mostra", "Mark Simonson"), ("Requiem", "Jonathan Hoefler"),
    # — expansion saturation round 32 (2026-06-27 run autonome, maintenance) : type designers solo (gap-filtré) —
    ("Brandon Grotesque", "Hannes von Döhren"), ("FF DIN", "Albert-Jan Pool"), ("Klavika", "Eric Olson"),
    ("Freight", "Joshua Darden"), ("Gentium", "Victor Gaultney"), ("Vollkorn", "Friedrich Althausen"),
    ("Source Sans Pro", "Paul Hunt"), ("Inter", "Rasmus Andersson"), ("Work Sans", "Wei Huang"),
    ("Cabin", "Pablo Impallari"), ("Lobster", "Pablo Impallari"), ("Montserrat", "Julieta Ulanovsky"),
    ("Museo", "Jos Buivenga"), ("Calluna", "Jos Buivenga"), ("Quicksand", "Andrew Paglinawan"),
    ("Oswald", "Vernon Adams"), ("Cardo", "David Perry"),
    # — expansion saturation round 54 (2026-06-27 run autonome, maintenance) : type designers solo (gap-filtré) —
    ("Bickham Script", "Richard Lipton"), ("Sloop", "Richard Lipton"), ("Tarzana", "Zuzana Licko"),
    ("Journal", "Zuzana Licko"), ("FF Blur", "Neville Brody"), ("Industria", "Neville Brody"),
    ("Arcadia", "Neville Brody"), ("Template Gothic", "Barry Deck"), ("Keedy Sans", "Jeffery Keedy"),
    ("Verlag", "Jonathan Hoefler"), ("Knockout", "Jonathan Hoefler"), ("Founders Grotesk", "Kris Sowersby"),
    ("Tiempos", "Kris Sowersby"), ("Metric", "Kris Sowersby"), ("Acumin", "Robert Slimbach"),
    ("Trade Gothic", "Jackson Burke"), ("Bryant", "Eric Olson"),
    # — expansion saturation round 74 (2026-06-28 run autonome, maintenance) : type designers solo (gap-filtré) —
    ("Seria", "Martin Majoor"), ("Nexus", "Martin Majoor"), ("Renard", "Fred Smeijers"), ("Arnhem", "Fred Smeijers"),
    ("Custodia", "Fred Smeijers"), ("PMN Caecilia", "Peter Matthias Noordzij"), ("Marian", "Paul Barnes"),
    ("Dala Floda", "Paul Barnes"), ("FF Trixie", "Erik van Blokland"), ("Big Caslon", "Matthew Carter"),
    ("Sitka", "Matthew Carter"), ("Retina", "Tobias Frere-Jones"), ("Mallory", "Tobias Frere-Jones"),
    ("Exchange", "Tobias Frere-Jones"), ("Documenta", "Frank Blokland"),
    # — expansion saturation round 92 (2026-06-28 run autonome, maintenance) : type designers solo (gap-filtré) —
    ("Thesis", "Lucas de Groot"), ("Taz", "Lucas de Groot"), ("Akko", "Akira Kobayashi"), ("Clifford", "Akira Kobayashi"),
    ("Conduit", "Mark van Bronkhorst"), ("Whitman", "Kent Lew"), ("Brothers", "John Downer"), ("GT Walsheim", "Noël Leu"),
    ("Druk", "Berton Hasebe"), ("Platform", "Berton Hasebe"), ("Union", "Radim Pesko"), ("Harlow", "Colin Brignall"),
    ("Aachen", "Colin Brignall"), ("Superstar", "Colin Brignall"), ("Italia", "Colin Brignall"), ("Revue", "Colin Brignall"),
    # — expansion saturation round 101 (2026-06-28 run autonome, maintenance) : type designers solo (gap-filtré) —
    ("Proforma", "Petr van Blokland"), ("Dante", "Giovanni Mardersteig"), ("Griffo", "Giovanni Mardersteig"),
    ("Hunt Roman", "Hermann Zapf"), ("Michelangelo", "Hermann Zapf"), ("Sistina", "Hermann Zapf"), ("Saphir", "Hermann Zapf"),
    ("Kompakt", "Hermann Zapf"), ("Cyclone", "Tobias Frere-Jones"), ("Niagara", "Tobias Frere-Jones"), ("Garage Gothic", "Tobias Frere-Jones"),
    ("Nobel", "Tobias Frere-Jones"), ("Citizen", "Zuzana Licko"), ("Lo-Res", "Zuzana Licko"), ("Solex", "Zuzana Licko"),
]


# ── CRÉATEUR DE LANGAGE DE PROGRAMMATION — Wikidata FR sparse ET bruitée (Q9143 : 34 ent. P170 / 149 P287,
#    fonc 85 % = équipes). CANON créateur UNIQUE incontesté ; DUOS/ÉQUIPES ÉCARTÉS (Go, Haskell, Lua, Erlang,
#    Objective-C, Prolog, Scheme, Simula, R, Julia, Kotlin, Dart, Smalltalk…) -> FAUX=0. Œuvre intellectuelle
#    attribuable (même esprit que jeux vidéo / police d'écriture). ──────────────────────────────────────────
LANGAGES = [
    ("Python", "Guido van Rossum"), ("C", "Dennis Ritchie"), ("B", "Ken Thompson"),
    ("C++", "Bjarne Stroustrup"), ("JavaScript", "Brendan Eich"), ("Java", "James Gosling"),
    ("Ruby", "Yukihiro Matsumoto"), ("PHP", "Rasmus Lerdorf"), ("Perl", "Larry Wall"),
    ("Rust", "Graydon Hoare"),
    ("Pascal", "Niklaus Wirth"), ("Modula-2", "Niklaus Wirth"), ("Oberon", "Niklaus Wirth"),
    ("Fortran", "John Backus"), ("Lisp", "John McCarthy"),
    ("Scala", "Martin Odersky"), ("Clojure", "Rich Hickey"), ("Swift", "Chris Lattner"),
    ("TypeScript", "Anders Hejlsberg"), ("C#", "Anders Hejlsberg"), ("Turbo Pascal", "Anders Hejlsberg"),
    ("APL", "Kenneth E. Iverson"), ("Tcl", "John Ousterhout"), ("Eiffel", "Bertrand Meyer"),
    ("D", "Walter Bright"), ("MATLAB", "Cleve Moler"), ("Forth", "Charles H. Moore"),
    ("F#", "Don Syme"), ("Bash", "Brian Fox"), ("Standard ML", "Robin Milner"),
    ("BCPL", "Martin Richards"), ("Wolfram Language", "Stephen Wolfram"),
    ("CoffeeScript", "Jeremy Ashkenas"), ("Elm", "Evan Czaplicki"), ("Nim", "Andreas Rumpf"),
    ("Zig", "Andrew Kelley"), ("Groovy", "James Strachan"), ("Io", "Steve Dekorte"),
    ("Factor", "Slava Pestov"), ("REBOL", "Carl Sassenrath"), ("Brainfuck", "Urban Müller"),
    ("Haxe", "Nicolas Cannasse"), ("SuperCollider", "James McCartney"),
    ("TeX", "Donald Knuth"), ("METAFONT", "Donald Knuth"),
    # — expansion saturation (2026-06-26 loop) : créateurs uniques (comités/duos écartés) —
    ("Ada", "Jean Ichbiah"), ("sed", "Lee E. McMahon"), ("Verilog", "Phil Moorby"),
    ("Ceylon", "Gavin King"), ("Pure Data", "Miller Puckette"), ("Csound", "Barry Vercoe"),
    # — expansion saturation round 9 (2026-06-26 run autonome) : créateur UNIQUE incontesté (comités/duos écartés) —
    ("Odin", "Ginger Bill"), ("PureScript", "Phil Freeman"), ("Idris", "Edwin Brady"),
    ("Vala", "Jürg Billeter"), ("Squirrel", "Alberto Demichelis"), ("Red", "Nenad Rakočević"),
    ("Pony", "Sylvan Clebsch"), ("K", "Arthur Whitney"), ("AutoIt", "Jonathan Bennett"),
    # — expansion saturation round 33 (2026-06-27 run autonome, maintenance) : créateur unique (gap-filtré ; esolangs/IF) —
    ("Inform", "Graham Nelson"), ("Befunge", "Chris Pressey"), ("Malbolge", "Ben Olmstead"),
    ("LOLCODE", "Adam Lindsay"), ("Chef", "David Morgan-Mar"), ("Janet", "Calvin Rose"),
    ("Gleam", "Louis Pilfold"), ("Roc", "Richard Feldman"), ("Hare", "Drew DeVault"),
    ("ATS", "Hongwei Xi"), ("TADS", "Michael J. Roberts"),
    # — expansion saturation round 75 (2026-06-28 run autonome, maintenance) : créateur unique historique (gap-filtré) —
    ("Icon", "Ralph Griswold"), ("Miranda", "David Turner"), ("SASL", "David Turner"), ("KRC", "David Turner"),
    ("REXX", "Mike Cowlishaw"), ("NetRexx", "Mike Cowlishaw"), ("SETL", "Jack Schwartz"), ("Comal", "Børge Christensen"),
    ("Frink", "Alan Eliasen"), ("Cecil", "Craig Chambers"), ("BlitzBasic", "Mark Sibly"), ("PureBasic", "Frédéric Laboureur"),
    ("Euphoria", "Robert Craig"), ("GameMaker Language", "Mark Overmars"),
    # — expansion saturation round 93 (2026-06-28 run autonome, maintenance) : créateur unique (gap-filtré) —
    ("4D", "Laurent Ribardière"), ("PowerShell", "Jeffrey Snover"), ("Genie", "Jamie McCracken"), ("Boo", "Rodrigo B. de Oliveira"),
    ("Cobra", "Charles Esterbrook"), ("Cat", "Christopher Diggins"), ("Mojo", "Chris Lattner"), ("Verse", "Tim Sweeney"),
    ("UnrealScript", "Tim Sweeney"), ("AngelScript", "Andreas Jönsson"), ("Ring", "Mahmoud Fayed"),
    # — expansion saturation round 52 (2026-06-27 run autonome, maintenance) : créateur unique (gap-filtré) —
    ("ReasonML", "Jordan Walke"), ("Koka", "Daan Leijen"), ("Lean", "Leonardo de Moura"),
    ("Dafny", "Rustan Leino"), ("Boogie", "Rustan Leino"), ("Frege", "Ingo Wechsung"),
    ("Wren", "Bob Nystrom"), ("Magpie", "Bob Nystrom"), ("E (langage)", "Mark S. Miller"),
    ("Joy", "Manfred von Thun"), ("NewLISP", "Lutz Mueller"), ("PicoLisp", "Alexander Burger"),
    ("Arc", "Paul Graham"), ("Bel", "Paul Graham"), ("Shen", "Mark Tarver"),
    ("Qi", "Mark Tarver"), ("Logtalk", "Paulo Moura"), ("Pure", "Albert Gräf"),
]


# ── CRÉATEUR DE SÉRIE TÉLÉVISÉE (showrunner/créateur) — Wikidata `createur_serie` P170 REJETÉ (ratio 0.73
#    fonc 86 %). CANON créateur UNIQUE incontesté ; DUOS/ÉQUIPES ÉCARTÉS (Game of Thrones=Benioff+Weiss,
#    Friends, Lost, Stranger Things=Duffer, Sherlock=Moffat+Gatiss, True Blood…) -> FAUX=0. ──────────────────
SERIES_TV = [
    ("Breaking Bad", "Vince Gilligan"), ("The Wire", "David Simon"), ("Les Soprano", "David Chase"),
    ("Mad Men", "Matthew Weiner"), ("Black Mirror", "Charlie Brooker"), ("Chernobyl", "Craig Mazin"),
    ("The Crown", "Peter Morgan"), ("Succession", "Jesse Armstrong"), ("Dr House", "David Shore"),
    ("Fargo", "Noah Hawley"), ("The Shield", "Shawn Ryan"), ("Deadwood", "David Milch"),
    ("Six Feet Under", "Alan Ball"), ("True Detective", "Nic Pizzolatto"), ("Vikings", "Michael Hirst"),
    ("Peaky Blinders", "Steven Knight"), ("Sons of Anarchy", "Kurt Sutter"),
    ("Fleabag", "Phoebe Waller-Bridge"), ("Dexter", "James Manos Jr."), ("Oz", "Tom Fontana"),
    ("Mindhunter", "Joe Penhall"), ("The Handmaid's Tale", "Bruce Miller"), ("Euphoria", "Sam Levinson"),
    ("Atlanta", "Donald Glover"), ("Girls", "Lena Dunham"), ("Veep", "Armando Iannucci"),
    ("Downton Abbey", "Julian Fellowes"), ("House of Cards", "Beau Willimon"),
    ("Broadchurch", "Chris Chibnall"), ("Luther", "Neil Cross"),
    ("Buffy contre les vampires", "Joss Whedon"), ("Firefly", "Joss Whedon"),
    ("Community", "Dan Harmon"), ("Les Simpson", "Matt Groening"), ("Les Griffin", "Seth MacFarlane"),
    ("BoJack Horseman", "Raphael Bob-Waksberg"), ("The Mandalorian", "Jon Favreau"),
    ("Mr. Robot", "Sam Esmail"), ("Supernatural", "Eric Kripke"), ("Californication", "Tom Kapinos"),
    ("Prison Break", "Paul Scheuring"), ("Heroes", "Tim Kring"), ("Hannibal", "Bryan Fuller"),
    ("Severance", "Dan Erickson"), ("The White Lotus", "Mike White"), ("La Casa de Papel", "Álex Pina"),
    ("À la Maison-Blanche", "Aaron Sorkin"), ("The Newsroom", "Aaron Sorkin"),
    # — expansion saturation (2026-06-26 loop) : créateur/showrunner unique (duos écartés) —
    ("The Boys", "Eric Kripke"), ("The Office (US)", "Greg Daniels"), ("The Good Place", "Michael Schur"),
    ("Curb Your Enthusiasm", "Larry David"), ("It's Always Sunny in Philadelphia", "Rob McElhenney"),
    ("Scrubs", "Bill Lawrence"), ("Misfits", "Howard Overman"), ("Utopia", "Dennis Kelly"),
    ("Top Boy", "Ronan Bennett"), ("This Is Us", "Dan Fogelman"), ("The Bear", "Christopher Storer"),
    ("Boardwalk Empire", "Terence Winter"), ("Ray Donovan", "Ann Biderman"), ("Entourage", "Doug Ellin"),
    ("Friday Night Lights", "Peter Berg"), ("Gilmore Girls", "Amy Sherman-Palladino"),
    ("The Marvelous Mrs. Maisel", "Amy Sherman-Palladino"), ("Justified", "Graham Yost"),
    ("Person of Interest", "Jonathan Nolan"),
    # — expansion saturation round 4 (2026-06-26 loop) : créateur/showrunner unique récent (duos écartés) —
    ("Reacher", "Nick Santora"), ("Andor", "Tony Gilroy"), ("Ripley", "Steven Zaillian"),
    ("Beef", "Lee Sung Jin"), ("The Penguin", "Lauren LeFranc"), ("Baby Reindeer", "Richard Gadd"),
    ("Happy Valley", "Sally Wainwright"), ("Last Tango in Halifax", "Sally Wainwright"),
    ("Gentleman Jack", "Sally Wainwright"), ("Line of Duty", "Jed Mercurio"), ("Bodyguard", "Jed Mercurio"),
    ("Mare of Easttown", "Brad Ingelsby"), ("The Diplomat", "Debora Cahn"), ("Poker Face", "Rian Johnson"),
    ("Giri/Haji", "Joe Barton"), ("Mr Bates vs The Post Office", "Gwyneth Hughes"),
    # — expansion saturation round 8 (2026-06-26 run autonome) : créateur/showrunner UNIQUE (duos/équipes écartés) —
    ("Watchmen", "Damon Lindelof"), ("Arrested Development", "Mitchell Hurwitz"), ("30 Rock", "Tina Fey"),
    ("Sex and the City", "Darren Star"), ("Beverly Hills, 90210", "Darren Star"), ("Emily in Paris", "Darren Star"),
    ("Dawson's Creek", "Kevin Williamson"),
    ("Grey's Anatomy", "Shonda Rhimes"), ("Scandal", "Shonda Rhimes"), ("Private Practice", "Shonda Rhimes"),
    ("How to Get Away with Murder", "Peter Nowalk"),
    ("The Witcher", "Lauren Schmidt Hissrich"), ("Squid Game", "Hwang Dong-hyuk"),
    ("The Thick of It", "Armando Iannucci"), ("Death in Paradise", "Robert Thorogood"),
    ("Nip/Tuck", "Ryan Murphy"), ("Detectorists", "Mackenzie Crook"), ("The IT Crowd", "Graham Linehan"),
    ("After Life", "Ricky Gervais"), ("Derek", "Ricky Gervais"),
    ("Chewing Gum", "Michaela Coel"), ("I May Destroy You", "Michaela Coel"),
    ("Sex Education", "Laurie Nunn"), ("Heartstopper", "Alice Oseman"),
    ("Stath Lets Flats", "Jamie Demetriou"), ("Patriot", "Steven Conrad"), ("Rectify", "Ray McKinnon"),
    # — expansion saturation round 17 (2026-06-26 run autonome) : créateur UNIQUE (gap-filtré ; duos écartés) —
    ("Picket Fences", "David E. Kelley"), ("Ally McBeal", "David E. Kelley"),
    ("Boston Legal", "David E. Kelley"), ("The Practice", "David E. Kelley"),
    ("Big Little Lies", "David E. Kelley"), ("Chicago Hope", "David E. Kelley"),
    ("The X-Files", "Chris Carter"), ("Millennium", "Chris Carter"),
    ("Dollhouse", "Joss Whedon"), ("Louie", "Louis C.K."), ("Carnivàle", "Daniel Knauf"),
    ("Spartacus", "Steven S. DeKnight"), ("Parenthood", "Jason Katims"),
    ("Bunheads", "Amy Sherman-Palladino"), ("Kim's Convenience", "Ins Choi"),
    ("Letterkenny", "Jared Keeso"), ("Continuum", "Simon Barry"), ("Travelers", "Brad Wright"),
    ("Farscape", "Rockne S. O'Bannon"), ("Raised by Wolves", "Aaron Guzikowski"),
    ("See", "Steven Knight"), ("Battlestar Galactica (2004)", "Ronald D. Moore"),
    ("Outlander", "Ronald D. Moore"),
    # — expansion saturation round 31 (2026-06-27 run autonome, maintenance) : créateur UNIQUE (gap-filtré) —
    ("Treme", "David Simon"), ("Show Me a Hero", "David Simon"), ("Avenue 5", "Armando Iannucci"),
    ("Crashing", "Phoebe Waller-Bridge"), ("Dead to Me", "Liz Feldman"), ("Dead Set", "Charlie Brooker"),
    ("The Tick", "Ben Edlund"), ("Pushing Daisies", "Bryan Fuller"),
    ("Babylon 5", "J. Michael Straczynski"), ("Daredevil", "Drew Goddard"),
    ("The Haunting of Hill House", "Mike Flanagan"), ("Midnight Mass", "Mike Flanagan"),
    ("The Fall of the House of Usher", "Mike Flanagan"), ("Invincible", "Robert Kirkman"),
    ("Legion", "Noah Hawley"), ("The Undoing", "David E. Kelley"), ("Silo", "Graham Yost"),
    ("The Killing", "Søren Sveistrup"), ("The Bridge (Bron/Broen)", "Hans Rosenfeldt"),
    ("Marcella", "Hans Rosenfeldt"), ("Le Bureau des légendes", "Éric Rochant"),
    ("Braquo", "Olivier Marchal"), ("Dix pour cent", "Fanny Herrero"),
    # — expansion saturation round 37 (2026-06-27 run autonome, maintenance) : créateur UNIQUE classiques+modernes (gap-filtré) —
    ("The Twilight Zone", "Rod Serling"), ("Night Gallery", "Rod Serling"), ("The Fugitive", "Roy Huggins"),
    ("Maverick", "Roy Huggins"), ("Quantum Leap", "Donald P. Bellisario"), ("JAG", "Donald P. Bellisario"),
    ("Knight Rider", "Glen A. Larson"), ("Battlestar Galactica (1978)", "Glen A. Larson"),
    ("Kojak", "Abby Mann"), ("Hawaii Five-O (1968)", "Leonard Freeman"),
    ("The Rehearsal", "Nathan Fielder"), ("How To with John Wilson", "John Wilson"),
    ("What We Do in the Shadows", "Jemaine Clement"), ("Wellington Paranormal", "Jemaine Clement"),
    ("Our Flag Means Death", "David Jenkins"), ("Abbott Elementary", "Quinta Brunson"),
    ("Random Acts of Flyness", "Terence Nance"), ("Lovecraft Country", "Misha Green"),
    ("Godless", "Scott Frank"), ("Pachinko", "Soo Hugh"), ("Tokyo Vice", "J.T. Rogers"),
    # — expansion saturation round 42 (2026-06-27 run autonome, maintenance) : créateur UNIQUE britannique (gap-filtré) —
    ("Foyle's War", "Anthony Horowitz"), ("Collateral", "David Hare"), ("The Hour", "Abi Morgan"),
    ("River", "Abi Morgan"), ("Doctor Foster", "Mike Bartlett"), ("Press", "Mike Bartlett"),
    ("Spooks", "David Wolstencroft"), ("Hustle", "Tony Jordan"), ("Years and Years", "Russell T Davies"),
    ("It's a Sin", "Russell T Davies"), ("Queer as Folk", "Russell T Davies"), ("Cucumber", "Russell T Davies"),
    ("Torchwood", "Russell T Davies"), ("Unforgotten", "Chris Lang"), ("The Fall", "Allan Cubitt"),
    ("Call the Midwife", "Heidi Thomas"),
    # — expansion saturation round 48 (2026-06-27 run autonome, maintenance) : créateur d'animation UNIQUE (gap-filtré) —
    ("Adventure Time", "Pendleton Ward"), ("Steven Universe", "Rebecca Sugar"), ("Gravity Falls", "Alex Hirsch"),
    ("The Amazing World of Gumball", "Ben Bocquelet"), ("Regular Show", "J.G. Quintel"),
    ("Over the Garden Wall", "Patrick McHale"), ("Bob's Burgers", "Loren Bouchard"),
    ("Samurai Jack", "Genndy Tartakovsky"), ("Dexter's Laboratory", "Genndy Tartakovsky"),
    ("Primal", "Genndy Tartakovsky"), ("The Powerpuff Girls", "Craig McCracken"),
    ("Foster's Home for Imaginary Friends", "Craig McCracken"), ("Courage the Cowardly Dog", "John R. Dilworth"),
    ("SpongeBob SquarePants", "Stephen Hillenburg"), ("Ren & Stimpy", "John Kricfalusi"),
    ("Rocko's Modern Life", "Joe Murray"), ("Invader Zim", "Jhonen Vasquez"), ("Æon Flux", "Peter Chung"),
    ("Beavis and Butt-Head", "Mike Judge"), ("Castlevania", "Warren Ellis"),
    # — expansion saturation round 53 (2026-06-27 run autonome, maintenance) : créateur UNIQUE (gap-filtré) —
    ("Good Omens", "Neil Gaiman"), ("Shadow and Bone", "Eric Heisserer"), ("Constellation", "Peter Harness"),
    ("Bodies", "Paul Tomalin"), ("The Capture", "Ben Chanan"), ("Vigil", "Tom Edge"),
    ("The Lazarus Project", "Joe Barton"), ("This Is England", "Shane Meadows"), ("The Virtues", "Shane Meadows"),
    ("Help", "Jack Thorne"), ("The Accident", "Jack Thorne"), ("Kiri", "Jack Thorne"),
    ("National Treasure", "Jack Thorne"), ("Patrick Melrose", "David Nicholls"), ("Three Girls", "Nicole Taylor"),
    # — expansion saturation round 60 (2026-06-27 run autonome, maintenance) : créateur UNIQUE sitcom (gap-filtré) —
    ("Malcolm in the Middle", "Linwood Boomer"), ("My Name Is Earl", "Greg Garcia"), ("Raising Hope", "Greg Garcia"),
    ("Everybody Loves Raymond", "Philip Rosenthal"), ("Spin City", "Gary David Goldberg"),
    ("Family Ties", "Gary David Goldberg"), ("Roseanne", "Matt Williams"), ("Coach", "Barry Kemp"),
    ("Murphy Brown", "Diane English"), ("Designing Women", "Linda Bloodworth-Thomason"),
    # — expansion saturation round 72 (2026-06-28 run autonome, maintenance) : créateur UNIQUE international (gap-filtré) —
    ("The Young Pope", "Paolo Sorrentino"), ("The New Pope", "Paolo Sorrentino"), ("Trapped", "Baltasar Kormákur"),
    ("1864", "Ole Bornedal"), ("Ragnarök", "Adam Price"), ("Biohackers", "Christian Ditter"),
    ("When Heroes Fly", "Omri Givon"), ("Hatufim", "Gideon Raff"), ("Hierro", "Pepe Coira"), ("Hippocrate", "Thomas Lilti"),
    # — expansion saturation round 90 (2026-06-28 run autonome, maintenance) : créateur UNIQUE (gap-filtré) —
    ("True Blood", "Alan Ball"), ("Here and Now", "Alan Ball"), ("The Americans", "Joe Weisberg"),
    ("United States of Tara", "Diablo Cody"), ("Weeds", "Jenji Kohan"), ("Orange Is the New Black", "Jenji Kohan"),
    ("Boss", "Farhad Safinia"), ("The Killing (US)", "Veena Sud"), ("Lodge 49", "Jim Gavin"), ("Doom Patrol", "Jeremy Carver"),
    ("Being Human (UK)", "Toby Whithouse"), ("Shameless (UK)", "Paul Abbott"), ("State of Play", "Paul Abbott"), ("No Offence", "Paul Abbott"),
    # — expansion saturation round 98 (2026-06-28 run autonome, maintenance) : créateur UNIQUE (gap-filtré) —
    ("Boston Public", "David E. Kelley"), ("Harry's Law", "David E. Kelley"), ("Sports Night", "Aaron Sorkin"),
    ("Studio 60 on the Sunset Strip", "Aaron Sorkin"), ("Girls5eva", "Meredith Scardino"), ("This Way Up", "Aisling Bea"),
    ("Such Brave Girls", "Kat Sadler"), ("Man Down", "Greg Davies"), ("Bless the Harts", "Emily Spivey"),
    ("Inside Job", "Shion Takeuchi"), ("Tuca & Bertie", "Lisa Hanawalt"),
]


# ── CRÉATEUR DE LOGICIEL (application/outil emblématique, NON-jeu) — créateur UNIQUE incontesté ;
#    DUOS/ÉQUIPES ÉCARTÉS (Django=Holovaty+Willison, React/Angular=équipes, WordPress=Mullenweg+Little,
#    Wikipedia=Wales+Sanger, VLC=équipe). JEUX exclus (-> concepteur_jeu). FAUX=0. ────────────────────────
LOGICIELS = [
    ("Linux", "Linus Torvalds"), ("Git", "Linus Torvalds"),
    ("GNU Emacs", "Richard Stallman"), ("GCC", "Richard Stallman"),
    ("Vim", "Bram Moolenaar"), ("curl", "Daniel Stenberg"),
    ("SQLite", "D. Richard Hipp"), ("Redis", "Salvatore Sanfilippo"),
    ("Nginx", "Igor Sysoev"), ("Node.js", "Ryan Dahl"), ("jQuery", "John Resig"),
    ("Vue.js", "Evan You"), ("Ruby on Rails", "David Heinemeier Hansson"),
    ("Laravel", "Taylor Otwell"), ("Flask", "Armin Ronacher"),
    ("Arch Linux", "Judd Vinet"), ("Debian", "Ian Murdock"), ("Slackware", "Patrick Volkerding"),
    ("FFmpeg", "Fabrice Bellard"), ("QEMU", "Fabrice Bellard"),
    ("7-Zip", "Igor Pavlov"), ("WinRAR", "Eugene Roshal"),
    ("Blender", "Ton Roosendaal"), ("Bitcoin", "Satoshi Nakamoto"),
    # — expansion saturation (2026-06-26 loop) : créateur unique d'un logiciel emblématique (duos écartés) —
    ("Samba", "Andrew Tridgell"), ("Wget", "Hrvoje Nikšić"), ("htop", "Hisham Muhammad"),
    ("tmux", "Nicholas Marriott"), ("i3", "Michael Stapelberg"), ("ImageMagick", "John Cristy"),
    ("Pandoc", "John MacFarlane"), ("Hugo", "Steve Francia"), ("Syncthing", "Jakob Borg"),
    ("Calibre", "Kovid Goyal"), ("Zsh", "Paul Falstad"), ("Fish", "Axel Liljencrantz"),
    ("Caddy", "Matt Holt"), ("Homebrew", "Max Howell"), ("OBS Studio", "Hugh Bailey"),
    # — expansion saturation round 4 (2026-06-26 loop) : créateur unique (écosystème JS/outils ; duos écartés) —
    ("Svelte", "Rich Harris"), ("Rollup", "Rich Harris"), ("Webpack", "Tobias Koppers"),
    ("Babel", "Sebastian McKenzie"), ("Deno", "Ryan Dahl"), ("Bun", "Jarred Sumner"),
    ("Prettier", "James Long"), ("esbuild", "Evan Wallace"), ("MobX", "Michel Weststrate"),
    ("Lodash", "John-David Dalton"), ("Moment.js", "Tim Wood"), ("Three.js", "Ricardo Cabello"),
    ("Tailwind CSS", "Adam Wathan"), ("Alpine.js", "Caleb Porzio"), ("htmx", "Carson Gross"),
    ("Express.js", "TJ Holowaychuk"), ("Sinatra", "Blake Mizerany"), ("Mercurial", "Matt Mackall"),
    ("Mono", "Miguel de Icaza"),
    # — expansion saturation round 8 (2026-06-26 run autonome) : créateur UNIQUE incontesté (duos/équipes écartés) —
    ("Docker", "Solomon Hykes"), ("Notepad++", "Don Ho"), ("MAME", "Nicola Salmoria"),
    ("Elasticsearch", "Shay Banon"), ("Bash", "Brian Fox"), ("Sed", "Lee McMahon"),
    ("less", "Mark Nudelman"), ("GnuPG", "Werner Koch"), ("Jenkins", "Kohsuke Kawaguchi"),
    ("Gentoo Linux", "Daniel Robbins"), ("MINIX", "Andrew Tanenbaum"),
    ("TeX", "Donald Knuth"), ("Metafont", "Donald Knuth"), ("LaTeX", "Leslie Lamport"),
    ("Drupal", "Dries Buytaert"), ("KeePass", "Dominik Reichl"), ("youtube-dl", "Ricardo Garcia"),
    ("AutoHotkey", "Chris Mallett"), ("uBlock Origin", "Raymond Hill"), ("Far Manager", "Eugene Roshal"),
    # — expansion saturation round 18 (2026-06-26 run autonome) : créateur UNIQUE incontesté (gap-filtré) —
    ("npm", "Isaac Schlueter"), ("PuTTY", "Simon Tatham"), ("FileZilla", "Tim Kosse"),
    ("qBittorrent", "Christophe Dumez"), ("Paint.NET", "Rick Brewster"), ("IrfanView", "Irfan Skiljan"),
    ("Total Commander", "Christian Ghisler"), ("WinSCP", "Martin Přikryl"), ("Everything", "David Carpenter"),
    ("Sublime Text", "Jon Skinner"), ("Mutt", "Michael Elkins"), ("ngrok", "Alan Shreve"),
    ("HAProxy", "Willy Tarreau"), ("Varnish", "Poul-Henning Kamp"), ("Wireshark", "Gerald Combs"),
    ("Nmap", "Gordon Lyon"), ("Metasploit", "H. D. Moore"), ("Snort", "Martin Roesch"),
    ("OpenVPN", "James Yonan"), ("WireGuard", "Jason A. Donenfeld"),
    # — expansion saturation round 30 (2026-06-27 run autonome, maintenance) : créateur UNIQUE (gap-filtré) —
    ("Vagrant", "Mitchell Hashimoto"), ("Terraform", "Mitchell Hashimoto"),
    ("ripgrep", "Andrew Gallant"), ("fd", "David Peter"), ("bat", "David Peter"),
    ("fzf", "Junegunn Choi"), ("jq", "Stephen Dolan"), ("zoxide", "Ajeet D'Souza"),
    ("Alacritty", "Joe Wilm"), ("Helix", "Blaž Hrastnik"), ("HTTPie", "Jakub Roztočil"),
    ("Requests", "Kenneth Reitz"), ("Celery", "Ask Solem"), ("NumPy", "Travis Oliphant"),
    ("pandas", "Wes McKinney"), ("Matplotlib", "John D. Hunter"), ("IPython", "Fernando Pérez"),
    ("FastAPI", "Sebastián Ramírez"), ("Pydantic", "Samuel Colvin"), ("Poetry", "Sébastien Eustace"),
    ("pytest", "Holger Krekel"), ("BeautifulSoup", "Leonard Richardson"),
    # — expansion saturation round 39 (2026-06-27 run autonome, maintenance) : créateur unique (gap-filtré) —
    ("Ansible", "Michael DeHaan"), ("Grafana", "Torkel Ödegaard"), ("Memcached", "Brad Fitzpatrick"),
    ("Traefik", "Emile Vauge"), ("Shotcut", "Dan Dennedy"), ("OpenShot", "Jonathan Thomas"),
    ("Stellarium", "Fabien Chéreau"), ("Celestia", "Chris Laurel"), ("KiCad", "Jean-Pierre Charras"),
    ("OpenSCAD", "Marius Kintel"), ("p5.js", "Lauren McCarthy"), ("Ardour", "Paul Davis"),
    ("MuseScore", "Werner Schweer"), ("Anki", "Damien Elmes"), ("Joplin", "Laurent Cozic"),
    ("Bitwarden", "Kyle Spearrin"), ("Aircrack-ng", "Thomas d'Otreppe"), ("John the Ripper", "Alexander Peslyak"),
    ("Hashcat", "Jens Steube"), ("Burp Suite", "Dafydd Stuttard"),
    # — expansion saturation round 47 (2026-06-27 run autonome, maintenance) : créateur unique JS/web (gap-filtré) —
    ("Jekyll", "Tom Preston-Werner"), ("Eleventy", "Zach Leatherman"), ("WezTerm", "Wez Furlong"),
    ("Kitty", "Kovid Goyal"), ("SolidJS", "Ryan Carniato"), ("Preact", "Jason Miller"),
    ("Axios", "Matt Zabriskie"), ("Chart.js", "Nick Downie"), ("D3.js", "Mike Bostock"),
    ("Leaflet", "Volodymyr Agafonkin"), ("Socket.IO", "Guillermo Rauch"), ("PM2", "Alexandre Strzelewicz"),
    ("Nodemon", "Remy Sharp"), ("Grunt", "Ben Alman"), ("Gulp", "Eric Schoffstall"),
    ("pnpm", "Zoltan Kochan"), ("Vite", "Evan You"), ("Parcel", "Devon Govett"),
    ("PostCSS", "Andrey Sitnik"), ("Autoprefixer", "Andrey Sitnik"),
    # — expansion saturation round 57 (2026-06-27 run autonome, maintenance) : créateur unique JS/Python (gap-filtré) —
    ("Zod", "Colin McDonnell"), ("tRPC", "Alex Johansson"), ("Turborepo", "Jared Palmer"), ("Formik", "Jared Palmer"),
    ("Jotai", "Daishi Kato"), ("Zustand", "Daishi Kato"), ("Valtio", "Daishi Kato"),
    ("TanStack Query", "Tanner Linsley"), ("TanStack Table", "Tanner Linsley"), ("Tone.js", "Yotam Mann"),
    ("Howler.js", "James Simpson"), ("Phaser", "Richard Davey"), ("Matter.js", "Liam Brummitt"),
    ("Hexo", "Tommy Chen"), ("Lektor", "Armin Ronacher"), ("structlog", "Hynek Schlawack"),
    ("Rich", "Will McGugan"), ("Textual", "Will McGugan"), ("Typer", "Sebastián Ramírez"),
    ("SQLModel", "Sebastián Ramírez"), ("Starlette", "Tom Christie"), ("Uvicorn", "Tom Christie"),
    # — expansion saturation round 78 (2026-06-28 run autonome, maintenance) : créateur unique (gap-filtré) —
    ("Ren'Py", "Tom Rothamel"), ("Twine", "Chris Klimas"), ("PICO-8", "Joseph White"), ("Aseprite", "David Capello"),
    ("REAPER", "Justin Frankel"), ("Winamp", "Justin Frankel"), ("Gnutella", "Justin Frankel"), ("SHOUTcast", "Justin Frankel"),
    ("foobar2000", "Peter Pawłowski"), ("gallery-dl", "Mike Fährmann"), ("Tampermonkey", "Jan Biniok"), ("Termux", "Fredrik Fornwall"),
    ("Tasker", "João Dias"), ("Rufus", "Pete Batard"), ("HWiNFO", "Martin Malík"), ("Process Explorer", "Mark Russinovich"),
    # — expansion saturation round 96 (2026-06-28 run autonome, maintenance) : créateur unique (gap-filtré) —
    ("Pygame", "Pete Shinners"), ("Nuitka", "Kay Hayen"), ("MicroPython", "Damien George"), ("PlatformIO", "Ivan Kravets"),
    ("Dear ImGui", "Omar Cornut"), ("Wings 3D", "Björn Gustavsson"), ("Sweet Home 3D", "Emmanuel Puybaret"), ("Synfig", "Robert Quattlebaum"),
    ("Tux Paint", "Bill Kendrick"), ("Battle for Wesnoth", "David White"), ("Simutrans", "Hansjörg Malthaner"), ("ADOM", "Thomas Biskup"),
    ("Cogmind", "Josh Ge"),
]


# ── INVENTEUR D'UN INSTRUMENT DE MUSIQUE (type d'instrument -> son inventeur UNIQUE indiscutable). Complète
#    le couloir instrument de T5 (facture instrumentale = fabricants/sociétés, vague17 ; ici = la PERSONNE qui
#    a inventé le TYPE). Œuvre technique attribuable (même esprit que createur_langage/police). FAUX=0 :
#    DISPUTÉS/PLURI-CLAIMANTS et DUOS ÉCARTÉS — harmonica (Buschmann disputé), accordéon (Demian + prédécesseurs),
#    bandonéon (développement diffus), Mellotron/Hang/cristal Baschet (équipes/duos), guitare/basse électrique
#    (paternité disputée Beauchamp/Rickenbacker/Fender). On n'inscrit que les inventeurs UNIQUES brevetés/établis. ──
INSTRUMENTS_INVENTEUR = [
    ("saxophone", "Adolphe Sax"), ("saxhorn", "Adolphe Sax"),
    ("thérémine", "Léon Theremin"),
    ("ondes Martenot", "Maurice Martenot"),
    ("orgue Hammond", "Laurens Hammond"),
    ("piano Rhodes", "Harold Rhodes"),
    ("célesta", "Auguste Mustel"),
    ("piano", "Bartolomeo Cristofori"),
    ("concertina", "Charles Wheatstone"),
    ("Chapman Stick", "Emmett Chapman"),
    ("harmonica de verre", "Benjamin Franklin"),
    ("synthétiseur Moog", "Robert Moog"),
    ("waterphone", "Richard Waters"),
    ("clavioline", "Constant Martin"),
    ("Ondioline", "Georges Jenny"),
    ("Telharmonium", "Thaddeus Cahill"),
    ("Trautonium", "Friedrich Trautwein"),
    # — expansion saturation (2026-06-26 loop) : inventeurs uniques certains —
    ("Stylophone", "Brian Jarvis"), ("violon Stroh", "Augustus Stroh"),
    ("octobasse", "Jean-Baptiste Vuillaume"), ("arpeggione", "Johann Georg Stauffer"),
    ("Novachord", "Laurens Hammond"),
    # — expansion saturation round 23 (2026-06-26 run autonome, maintenance) : inventeur unique certain —
    ("guitare à résonateur Dobro", "John Dopyera"), ("flûte système Boehm", "Theobald Boehm"),
    ("bugle à clés", "Joseph Halliday"), ("piano droit", "John Isaac Hawkins"),
    # — expansion saturation round 70 (2026-06-27 run autonome, maintenance) : inventeur unique d'instrument électronique (gap-filtré) —
    ("Buchla", "Don Buchla"), ("EMS VCS 3", "Peter Zinovieff"), ("Marimba Lumina", "Don Buchla"), ("Tannerin", "Paul Tanner"),
    # — expansion saturation round 36 (2026-06-27 run autonome, maintenance) : inventeur unique (gap-filtré) —
    ("Continuum", "Lippold Haken"), ("Eigenharp", "John Lambert"), ("Tenori-on", "Toshio Iwai"),
    ("Hydraulophone", "Steve Mann"), ("Daxophone", "Hans Reichel"), ("Pyrophone", "Frédéric Kastner"),
    ("Denis d'or", "Václav Prokop Diviš"), ("Luthéal", "Georges Cloetens"), ("Pianet", "Ernst Zacharias"),
]


# ── PARFUMEUR (le « nez ») D'UN PARFUM — composition olfactive = œuvre attribuable, aucune lane ne la couvre ;
#    Wikidata FR sparse sur parfum->créateur. CANON : attributions établies de l'histoire de la parfumerie,
#    parfumeur UNIQUE certain ; DUOS ÉCARTÉS (Opium=Amic+Sieuzac, CK One=Morillas+Frémont, Arpège=Fraysse+Vacher,
#    Pleasures=Buzantian+Morillas). Titres à mot commun QUALIFIÉS par la maison pour lever l'homonymie. ──────────
PARFUMS = [
    ("Chanel N°5", "Ernest Beaux"), ("Chanel N°19", "Henri Robert"),
    ("Shalimar", "Jacques Guerlain"), ("Mitsouko", "Jacques Guerlain"),
    ("Jicky", "Aimé Guerlain"),
    ("Eau Sauvage", "Edmond Roudnitska"), ("Diorissimo", "Edmond Roudnitska"),
    ("Femme de Rochas", "Edmond Roudnitska"),
    ("Fracas", "Germaine Cellier"), ("Bandit", "Germaine Cellier"), ("Vent Vert", "Germaine Cellier"),
    ("L'Air du Temps", "Francis Fabron"),
    ("Joy (Jean Patou)", "Henri Alméras"),
    ("Poison (Dior)", "Édouard Fléchier"),
    ("Trésor (Lancôme)", "Sophia Grojsman"),
    ("Angel (Mugler)", "Olivier Cresp"),
    ("Aromatics Elixir", "Bernard Chant"),
    # — expansion saturation (2026-06-26 loop) : nez uniques certains (titres ambigus qualifiés) —
    ("Coco Mademoiselle", "Jacques Polge"), ("Égoïste (Chanel)", "Jacques Polge"),
    ("Habit Rouge", "Jean-Paul Guerlain"), ("Vétiver (Guerlain)", "Jean-Paul Guerlain"),
    ("Samsara", "Jean-Paul Guerlain"), ("Nahéma", "Jean-Paul Guerlain"), ("Chamade", "Jean-Paul Guerlain"),
    ("Drakkar Noir", "Pierre Wargnye"), ("Cool Water", "Pierre Bourdon"), ("Kouros", "Pierre Bourdon"),
    # — expansion saturation round 5 (2026-06-26 loop) : nez uniques certains (titres ambigus qualifiés) —
    ("First (Van Cleef & Arpels)", "Jean-Claude Ellena"), ("Terre d'Hermès", "Jean-Claude Ellena"),
    ("L'Eau d'Issey", "Jacques Cavallier"), ("Flower by Kenzo", "Alberto Morillas"),
    ("Acqua di Giò", "Alberto Morillas"), ("Le Mâle (Jean Paul Gaultier)", "Francis Kurkdjian"),
    ("Baccarat Rouge 540", "Francis Kurkdjian"), ("Light Blue (Dolce & Gabbana)", "Olivier Cresp"),
    # — expansion saturation round 8 (2026-06-26 run autonome) : nez UNIQUE certain (titres ambigus qualifiés, duos écartés) —
    ("Obsession (Calvin Klein)", "Jean Guichard"), ("Eternity (Calvin Klein)", "Sophia Grojsman"),
    ("White Linen (Estée Lauder)", "Sophia Grojsman"), ("Paris (Yves Saint Laurent)", "Sophia Grojsman"),
    ("Calyx (Prescriptives)", "Sophia Grojsman"),
    ("Dune (Dior)", "Jean-Louis Sieuzac"), ("J'adore (Dior)", "Calice Becker"),
    ("Tommy Girl", "Calice Becker"),
    ("Allure (Chanel)", "Jacques Polge"), ("Coco (Chanel)", "Jacques Polge"),
    ("Bleu de Chanel", "Jacques Polge"), ("Antaeus (Chanel)", "Jacques Polge"),
    ("Noa (Cacharel)", "Olivier Cresp"),
    ("Lolita Lempicka", "Annick Menardo"), ("Hypnotic Poison (Dior)", "Annick Menardo"),
    ("Le Feu d'Issey", "Jacques Cavallier"),
    # — expansion saturation round 20 (2026-06-26 run autonome) : nez UNIQUE certain (gap-filtré ; titres qualifiés) —
    ("Gabrielle (Chanel)", "Olivier Polge"), ("Boy (Chanel)", "Olivier Polge"),
    ("Un Jardin sur le Nil", "Jean-Claude Ellena"), ("Déclaration (Cartier)", "Jean-Claude Ellena"),
    ("Cologne Bigarade", "Jean-Claude Ellena"), ("Mugler Cologne", "Alberto Morillas"),
    ("Aqua Universalis", "Francis Kurkdjian"), ("Grand Soir", "Francis Kurkdjian"),
    ("Nina (Nina Ricci)", "Olivier Cresp"), ("Yvresse (YSL)", "Sophia Grojsman"),
    ("Tocade (Rochas)", "Maurice Roucel"), ("Musc Ravageur", "Maurice Roucel"),
    ("Premier Figuier", "Olivia Giacobetti"), ("Portrait of a Lady", "Dominique Ropion"),
    ("Ysatis (Givenchy)", "Dominique Ropion"), ("Amarige (Givenchy)", "Dominique Ropion"),
    ("Ambre Sultan", "Christopher Sheldrake"), ("Diorella", "Edmond Roudnitska"),
    ("Eau d'Hermès", "Edmond Roudnitska"), ("Jolie Madame (Balmain)", "Germaine Cellier"),
    ("Cuir de Russie (Chanel)", "Ernest Beaux"), ("Bois des Îles (Chanel)", "Ernest Beaux"),
    # — expansion saturation round 36 (2026-06-27 run autonome, maintenance) : nez UNIQUE (gap-filtré ; titres qualifiés) —
    ("L'Eau d'Hiver", "Jean-Claude Ellena"), ("Voyage d'Hermès", "Jean-Claude Ellena"),
    ("Dans tes bras", "Maurice Roucel"), ("Insolence", "Maurice Roucel"),
    ("Une Fleur de Cassie", "Dominique Ropion"), ("Five o'Clock au Gingembre", "Christopher Sheldrake"),
    ("Misia (Chanel)", "Olivier Polge"), ("Bvlgari pour Femme", "Alberto Morillas"),
    ("Oud (MFK)", "Francis Kurkdjian"), ("Chanel N°22", "Ernest Beaux"),
    ("L'Heure Bleue", "Jacques Guerlain"), ("Vol de Nuit", "Jacques Guerlain"), ("Liu", "Jacques Guerlain"),
    ("Héritage (Guerlain)", "Jean-Paul Guerlain"), ("Jardins de Bagatelle", "Jean-Paul Guerlain"),
    ("Le Parfum de Thérèse", "Edmond Roudnitska"),
    # — expansion saturation round 43 (2026-06-27 run autonome, maintenance) : nez UNIQUE (gap-filtré ; titres qualifiés) —
    ("Angéliques sous la Pluie", "Jean-Claude Ellena"), ("Prada Infusion d'Iris", "Daniela Andrier"),
    ("Bulgari Black", "Annick Menardo"), ("Patou Pour Homme", "Annick Menardo"),
    ("La Panthère (Cartier)", "Mathilde Laurent"), ("Baiser Volé (Cartier)", "Mathilde Laurent"),
    ("Twilly d'Hermès", "Christine Nagel"), ("Idylle (Guerlain)", "Thierry Wasser"),
    ("Sécrétions Magnifiques", "Antoine Lie"), ("Timbuktu", "Bertrand Duchaufour"),
    ("Dzongkha", "Bertrand Duchaufour"), ("French Lover", "Pierre Bourdon"),
    ("Envy (Gucci)", "Maurice Roucel"), ("Rochas Man", "Maurice Roucel"),
    ("Jaipur (Boucheron)", "Sophia Grojsman"), ("Dzing!", "Olivia Giacobetti"),
    ("En Passant", "Olivia Giacobetti"),
    # — expansion saturation round 56 (2026-06-27 run autonome, maintenance) : nez UNIQUE (gap-filtré ; titres qualifiés) —
    ("Poivre Samarcande", "Jean-Claude Ellena"), ("Brin de Réglisse", "Jean-Claude Ellena"), ("Jour d'Hermès", "Christine Nagel"),
    ("L'Envol (Cartier)", "Mathilde Laurent"), ("Carat (Cartier)", "Mathilde Laurent"), ("Infusion d'Homme", "Daniela Andrier"),
    ("Iris Poudre", "Pierre Bourdon"), ("Gucci Rush", "Maurice Roucel"), ("Bois d'Argent (Dior)", "Annick Menardo"),
    ("Avignon", "Bertrand Duchaufour"), ("Stella", "Jacques Cavallier"), ("L'Eau d'Issey pour Homme", "Jacques Cavallier"),
    ("Bvlgari Omnia", "Alberto Morillas"), ("So Pretty (Cartier)", "Sophia Grojsman"), ("Philosykos", "Olivia Giacobetti"),
    ("Idole de Lubin", "Olivia Giacobetti"),
    # — expansion saturation round 80 (2026-06-28 run autonome, maintenance) : nez UNIQUE (gap-filtré ; titres qualifiés) —
    ("Chance (Chanel)", "Jacques Polge"), ("Allure Homme", "Jacques Polge"), ("Acqua di Giò Profumo", "Alberto Morillas"),
    ("L'Eau par Kenzo", "Alberto Morillas"), ("Fleur du Mâle", "Francis Kurkdjian"), ("Lumière Noire", "Francis Kurkdjian"),
    ("Amyris (MFK)", "Francis Kurkdjian"), ("Absolue pour le Soir", "Francis Kurkdjian"), ("Bel Ami (Hermès)", "Jean-Louis Sieuzac"),
    ("Halston Classic", "Bernard Chant"), ("Loulou (Cacharel)", "Jean Guichard"),
]


# ── AUTEUR D'UN JEU DE RÔLE SUR TABLE (tabletop RPG) — couloir jeux de T5 (distinct de auteur_jeu_societe =
#    plateau, et concepteur_jeu = vidéo). Wikidata FR sparse. CANON créateur UNIQUE certain ; ÉQUIPES/DUOS
#    ÉCARTÉS (D&D=Gygax+Arneson, Shadowrun/Paranoia/RuneQuest/Ars Magica/Werewolf… = équipes). HOMONYMES écartés
#    (Call of Cthulhu = nouvelle Lovecraft ; « Pendragon » = roman/groupe -> on garde le titre RPG complet). ──────
JEUX_ROLE = [
    ("Vampire: The Masquerade", "Mark Rein·Hagen"),
    ("GURPS", "Steve Jackson"),
    ("King Arthur Pendragon", "Greg Stafford"),
    ("Cyberpunk 2020", "Mike Pondsmith"),
    ("Tunnels & Trolls", "Ken St. Andre"),
    ("Empire of the Petal Throne", "M. A. R. Barker"),
    ("Everway", "Jonathan Tweet"),
    ("Talislanta", "Stephan Michael Sechi"),
    ("Rifts", "Kevin Siembieda"),
    # — expansion saturation (2026-06-26 loop) : auteurs uniques certains —
    ("Twilight: 2000", "Frank Chadwick"), ("Space: 1889", "Frank Chadwick"),
    ("DragonQuest", "Eric Goldberg"), ("Fudge", "Steffan O'Sullivan"),
    ("Blades in the Dark", "John Harper"), ("Fiasco", "Jason Morningstar"),
    ("Microscope", "Ben Robbins"),
    # — expansion saturation round 24 (2026-06-26 run autonome, maintenance) : auteur UNIQUE (équipes/duos écartés : Paranoia, Mage, Lancer, Toon) —
    ("Traveller", "Marc Miller"), ("Tales from the Loop", "Nils Hintze"),
    ("Mausritter", "Isaac Williams"), ("Numenera", "Monte Cook"),
    ("Stars Without Number", "Kevin Crawford"), ("Ironsworn", "Shawn Tomkin"),
    # — expansion saturation round 73 (2026-06-28 run autonome, maintenance) : auteur UNIQUE de JdR indé (gap-filtré) —
    ("Apocalypse World", "D. Vincent Baker"), ("Dread", "Epidiah Ravachol"), ("Lasers & Feelings", "John Harper"),
    ("Mouse Guard", "Luke Crane"), ("Burning Wheel", "Luke Crane"), ("The Quiet Year", "Avery Alder"),
    ("Monsterhearts", "Avery Alder"), ("Wanderhome", "Jay Dragon"), ("Thirsty Sword Lesbians", "April Kit Walsh"),
    ("Honey Heist", "Grant Howitt"), ("Goblin Quest", "Grant Howitt"), ("Ten Candles", "Stephen Dewey"),
]


# ── CRÉATEUR D'UN OBJET DE DESIGN ICONIQUE (mobilier/luminaire) — œuvre de design attribuable (précédent
#    createur_police = design typographique). Non couvert ailleurs. CANON designer UNIQUE certain ; DUOS ÉCARTÉS
#    (Eames=Charles+Ray, lampe Arco=frères Castiglioni) ; Barcelona ÉCARTÉE (co-attribution Lilly Reich documentée
#    = doute -> FAUX=0). ───────────────────────────────────────────────────────────────────────────────────────
OBJETS_DESIGN = [
    ("Chaise Wassily", "Marcel Breuer"), ("Chaise Cesca", "Marcel Breuer"),
    ("Fauteuil Egg", "Arne Jacobsen"), ("Fauteuil Swan", "Arne Jacobsen"), ("Chaise Fourmi", "Arne Jacobsen"),
    ("Chaise Panton", "Verner Panton"),
    ("Chaise Tulip", "Eero Saarinen"),
    ("Fauteuil Ball", "Eero Aarnio"),
    ("Chaise Louis Ghost", "Philippe Starck"),
    ("Chaise Zig-Zag", "Gerrit Rietveld"), ("Chaise rouge et bleue", "Gerrit Rietveld"),
    ("Chaise n° 14", "Michael Thonet"),
    ("Lampe Anglepoise", "George Carwardine"),
    ("Lampe Tizio", "Richard Sapper"),
    ("Chaise Wishbone", "Hans Wegner"),
    ("Chaise Diamond", "Harry Bertoia"),
    # — expansion saturation round 2 (2026-06-26 loop) : designer unique (duos écartés) —
    ("Tabouret Tam Tam", "Henry Massonnet"), ("Chaise Tripp Trapp", "Peter Opsvik"),
    ("Lampe Pipistrello", "Gae Aulenti"), ("Lampe Akari", "Isamu Noguchi"),
    ("Chaise Costes", "Philippe Starck"), ("Presse-citron Juicy Salif", "Philippe Starck"),
    ("Chaise Superleggera", "Gio Ponti"), ("Fauteuil Proust", "Alessandro Mendini"),
    ("Bibliothèque Carlton", "Ettore Sottsass"), ("Chaise Plia", "Giancarlo Piretti"),
    ("Lampe Eclisse", "Vico Magistretti"), ("Chaise Wiggle", "Frank Gehry"),
    ("Chaise Hill House", "Charles Rennie Mackintosh"),
    # — expansion saturation round 6 (2026-06-26 run autonome) : designer unique certain (duos/trios écartés) —
    ("Fauteuil Womb", "Eero Saarinen"), ("Cafetière Moka Express", "Alfonso Bialetti"),
    ("Chaise Paimio", "Alvar Aalto"), ("Tabouret 60", "Alvar Aalto"), ("Vase Savoy", "Alvar Aalto"),
    ("Tabouret Butterfly", "Sori Yanagi"), ("Lampe Gras", "Bernard-Albin Gras"),
    ("Lampe PH 5", "Poul Henningsen"), ("Chaise Cab", "Mario Bellini"),
    ("Chaise Selene", "Vico Magistretti"), ("Chaise Spaghetti", "Giandomenico Belotti"),
    # — expansion saturation round 15 (2026-06-26 run autonome) : designer UNIQUE certain (duos/trios écartés) —
    ("Chaise Standard", "Jean Prouvé"), ("Lampe Potence", "Jean Prouvé"),
    ("Fauteuil Bibendum", "Eileen Gray"), ("Table E-1027", "Eileen Gray"),
    ("Chaise A56", "Xavier Pauchard"), ("Chaise Polyprop", "Robin Day"),
    ("Lampe Jielde", "Jean-Louis Domecq"), ("Chaise Landi", "Hans Coray"),
    ("Bibliothèque Nuage", "Charlotte Perriand"), ("Lampe Bestlite", "Robert Dudley Best"),
    # — expansion saturation round 29 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Lampe Atollo", "Vico Magistretti"), ("Chaise Carimate", "Vico Magistretti"),
    ("Chaise Universale", "Joe Colombo"), ("Lampe Acrilica", "Joe Colombo"),
    ("Lampe Nesso", "Giancarlo Mattioli"), ("Chaise Tom Vac", "Ron Arad"),
    ("Bibliothèque Bookworm", "Ron Arad"), ("Air-Chair", "Jasper Morrison"),
    ("Tabouret Cork", "Jasper Morrison"), ("Chaise Myto", "Konstantin Grcic"),
    ("Chair One", "Konstantin Grcic"), ("Lockheed Lounge", "Marc Newson"),
    ("Fauteuil Embryo", "Marc Newson"), ("Chaise Garden Egg", "Peter Ghyczy"),
    # — expansion saturation round 81 (2026-06-28 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Lampe Bourgie", "Ferruccio Laviani"), ("Chaise Masters", "Philippe Starck"), ("Chaise Mademoiselle", "Philippe Starck"),
    ("Lampe Lampadina", "Achille Castiglioni"), ("Chaise Primate", "Achille Castiglioni"), ("Lampe Frisbi", "Achille Castiglioni"),
    ("Lampe Brera", "Achille Castiglioni"), ("Chaise Voido", "Ron Arad"), ("Chaise Nemo", "Fabio Novembre"),
    ("Cafetière La Conica", "Aldo Rossi"), ("Tabouret Plopp", "Oskar Zieta"),
    # — expansion saturation round 100 (2026-06-28 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Tabouret Componibili", "Anna Castelli Ferrieri"), ("Table à roulettes (Aulenti)", "Gae Aulenti"),
    ("Chaise Pastil", "Eero Aarnio"), ("Chaise Bubble", "Eero Aarnio"), ("Chaise Tomato", "Eero Aarnio"),
    ("Lampe PH Snowball", "Poul Henningsen"), ("Chaise Cone", "Verner Panton"), ("Chaise Heart Cone", "Verner Panton"),
    ("Lampe Flowerpot", "Verner Panton"), ("Lampe VP Globe", "Verner Panton"), ("Chariot Boby", "Joe Colombo"), ("Tube Chair", "Joe Colombo"),
    # — expansion saturation round 46 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Chaise Série 7", "Arne Jacobsen"), ("Chaise Grand Prix", "Arne Jacobsen"), ("Lampe AJ", "Arne Jacobsen"),
    ("Fauteuil PK22", "Poul Kjærholm"), ("Chaise Pelican", "Finn Juhl"), ("Chaise Chieftain", "Finn Juhl"),
    ("Fauteuil Papa Bear", "Hans Wegner"), ("Chaise Round", "Hans Wegner"), ("Chaise Shell", "Hans Wegner"),
    ("Lampe PH Artichaut", "Poul Henningsen"), ("Chaise J39", "Børge Mogensen"), ("Chaise Dr. No", "Philippe Starck"),
    ("Lampe Miss Sissi", "Philippe Starck"), ("Tabouret W.W.", "Philippe Starck"),
    ("Thinking Man's Chair", "Jasper Morrison"), ("Chaise Hal", "Jasper Morrison"), ("Chaise S", "Tom Dixon"),
    # — expansion saturation round 55 (2026-06-27 run autonome, maintenance) : designer unique (gap-filtré) —
    ("Lampe Tahiti", "Ettore Sottsass"), ("Casablanca", "Ettore Sottsass"), ("Chaise Knotted", "Marcel Wanders"),
    ("Lampe Skygarden", "Marcel Wanders"), ("Block Lamp", "Harri Koskinen"), ("Bouilloire 9093", "Michael Graves"),
    ("Chaise How High the Moon", "Shiro Kuramata"), ("Chaise Miss Blanche", "Shiro Kuramata"),
    ("Fauteuil Up", "Gaetano Pesce"), ("Chaise Feltri", "Gaetano Pesce"), ("Chaise Tongue", "Pierre Paulin"),
    ("Fauteuil Mushroom", "Pierre Paulin"), ("Fauteuil Ribbon", "Pierre Paulin"), ("Fauteuil Orange Slice", "Pierre Paulin"),
    ("Lampe Falkland", "Bruno Munari"), ("Lampe Costanza", "Paolo Rizzatto"),
    # — expansion saturation round 61 (2026-06-27 run autonome, maintenance) : design industriel/produit, designer unique (gap-filtré) —
    ("Montre Tank", "Louis Cartier"), ("Montre Santos", "Louis Cartier"), ("Stylo Bic Cristal", "László Bíró"),
    ("Vespa", "Corradino D'Ascanio"), ("Fiat 500", "Dante Giacosa"), ("Mini", "Alec Issigonis"), ("AeroPress", "Alan Adler"),
    ("Chaise Toledo", "Jorge Pensi"), ("Tabouret Bombo", "Stefano Giovannoni"), ("Chaise Magis Spun", "Thomas Heatherwick"),
    ("Fauteuil F51", "Walter Gropius"), ("Soft Big Easy", "Ron Arad"), ("Fauteuil Rover", "Ron Arad"),
    ("Chaise Argyle", "Charles Rennie Mackintosh"),
]


# ── CRÉATEUR D'UNE LANGUE CONSTRUITE (conlang) — langue artificielle = œuvre intellectuelle attribuable, non
#    couverte ailleurs ; DISTINCT de createur_langage_programmation (langage informatique). CANON créateur UNIQUE
#    certain ; ÉQUIPES/DUOS/RÉFORMES ÉCARTÉS (Ido = de Beaufront/Couturat + comité, Interlingua = IALA, Lojban =
#    Logical Language Group) -> FAUX=0. ───────────────────────────────────────────────────────────────────────
LANGUES_CONSTRUITES = [
    ("Espéranto", "Louis-Lazare Zamenhof"), ("Volapük", "Johann Martin Schleyer"),
    ("Klingon", "Marc Okrand"), ("Na'vi", "Paul Frommer"), ("Toki Pona", "Sonja Lang"),
    ("Quenya", "J. R. R. Tolkien"), ("Sindarin", "J. R. R. Tolkien"),
    ("Dothraki", "David J. Peterson"), ("Haut valyrien", "David J. Peterson"),
    ("Loglan", "James Cooke Brown"), ("Novial", "Otto Jespersen"),
    ("Lingua Franca Nova", "C. George Boeree"), ("Solresol", "François Sudre"),
    ("Láadan", "Suzette Haden Elgin"), ("Brithenig", "Andrew Smith"), ("Kotava", "Staren Fetcey"),
    # — expansion saturation round 68 (2026-06-27 run autonome, maintenance) : conlang à auteur unique (gap-filtré) —
    ("Interlingue (Occidental)", "Edgar de Wahl"), ("Ithkuil", "John Quijada"), ("Kēlen", "Sylvia Sotomayor"),
    ("Sambahsa", "Olivier Simon"), ("Talossan", "Robert Ben Madison"), ("Verdurian", "Mark Rosenfelder"),
    ("Wenedyk", "Jan van Steenbergen"), ("Trigedasleng", "David J. Peterson"), ("Castithan", "David J. Peterson"),
    ("Khuzdul", "J. R. R. Tolkien"), ("Adûnaic", "J. R. R. Tolkien"),
    # — expansion saturation round 86 (2026-06-28 run autonome, maintenance) : conlang à auteur unique (gap-filtré) —
    ("Valarin", "J. R. R. Tolkien"), ("Telerin", "J. R. R. Tolkien"), ("Lingua Ignota", "Hildegarde de Bingen"),
    ("Europanto", "Diego Marani"), ("aUI", "John W. Weilgart"), ("Babm", "Rikichi Okamoto"), ("Ro (langue)", "Edward Powell Foster"),
    ("Eurolengo", "Leslie Jones"), ("Dritok", "Donald Boozer"),
]


# ── CRÉATEUR (DESIGNER) D'UN LOGO ICONIQUE — identité visuelle = œuvre de design graphique attribuable, non
#    couverte ailleurs (précédents createur_police / objet_design / createur_serie). CANON designer UNIQUE
#    certain ; AGENCES/ÉQUIPES ÉCARTÉES (logo Twitter, MTV, Pepsi…) -> FAUX=0. ──────────────────────────────
LOGOS = [
    ("logo Nike", "Carolyn Davidson"), ("logo Apple", "Rob Janoff"),
    ("I Love New York (logo)", "Milton Glaser"), ("logo Coca-Cola", "Frank Mason Robinson"),
    ("logo Woolmark", "Francesco Saroglia"), ("logo Chupa Chups", "Salvador Dalí"),
    ("logo FedEx", "Lindon Leader"), ("logo Penguin Books", "Edward Young"),
    ("logo IBM", "Paul Rand"), ("logo ABC", "Paul Rand"), ("logo NeXT", "Paul Rand"),
    ("logo Westinghouse", "Paul Rand"), ("logo CBS", "William Golden"),
    ("roundel du métro de Londres", "Edward Johnston"), ("anneaux olympiques", "Pierre de Coubertin"),
    # — expansion saturation round 69 (2026-06-27 run autonome, maintenance) : designer unique de logo (gap-filtré) —
    ("logo Shell", "Raymond Loewy"), ("logo Lucky Strike", "Raymond Loewy"), ("logo Exxon", "Raymond Loewy"),
    ("logo United Airlines", "Saul Bass"), ("logo AT&T", "Saul Bass"), ("logo Continental Airlines", "Saul Bass"),
    ("logo Bell System", "Saul Bass"), ("logo Quaker Oats", "Saul Bass"),
    # — expansion saturation round 87 (2026-06-28 run autonome, maintenance) : designer unique de logo (gap-filtré) —
    ("logo Yale University Press", "Paul Rand"), ("logo Cummins", "Paul Rand"), ("logo Firefox", "Jon Hicks"),
    ("logo Munich 1972", "Otl Aicher"), ("pictogrammes des JO de 1972", "Otl Aicher"), ("logo Lufthansa", "Otl Aicher"),
    ("logo Deutsche Bank", "Anton Stankowski"), ("logo Motorola", "Morton Goldsholl"), ("logo Pirelli", "Bob Noorda"), ("logo Eni", "Luigi Broggini"),
]


# ── CHORÉGRAPHE D'UN BALLET — la chorégraphie (≠ la musique = compositeur_ballet) est une œuvre attribuable.
#    Wikidata FR ~0 entité. CANON : UNIQUEMENT le chorégraphe UNIQUE indiscutable de la création/version-repère ;
#    DUOS ÉCARTÉS (Giselle = Coralli+Perrot, Lac des cygnes = Petipa+Ivanov) ; revivals/versions multiples
#    ambigus écartés (Boléro, Roméo et Juliette) -> FAUX=0. ─────────────────────────────────────────────────────
CHOREGRAPHIES = [
    ("Le Sacre du printemps", "Vaslav Nijinsky"), ("L'Après-midi d'un faune", "Vaslav Nijinsky"),
    ("La Belle au bois dormant", "Marius Petipa"), ("La Bayadère", "Marius Petipa"),
    ("Raymonda", "Marius Petipa"), ("Don Quichotte (ballet)", "Marius Petipa"),
    ("Casse-Noisette", "Lev Ivanov"),
    ("Le Spectre de la rose", "Michel Fokine"), ("Les Sylphides", "Michel Fokine"),
    ("Petrouchka", "Michel Fokine"), ("L'Oiseau de feu", "Michel Fokine"),
    ("Apollon musagète", "George Balanchine"), ("Agon", "George Balanchine"),
    ("Le Fils prodigue", "George Balanchine"), ("Jewels", "George Balanchine"),
    ("Rodeo", "Agnes de Mille"), ("Appalachian Spring", "Martha Graham"),
    # — expansion saturation round 67 (2026-06-27 run autonome, maintenance) : chorégraphe UNIQUE (gap-filtré) —
    ("Schéhérazade", "Michel Fokine"), ("Le Carnaval", "Michel Fokine"), ("Sérénade", "George Balanchine"),
    ("Concerto Barocco", "George Balanchine"), ("Symphony in C", "George Balanchine"), ("Manon", "Kenneth MacMillan"),
    ("Mayerling", "Kenneth MacMillan"), ("La Fille mal gardée", "Frederick Ashton"), ("Marguerite and Armand", "Frederick Ashton"),
    ("Symphonic Variations", "Frederick Ashton"), ("Pillar of Fire", "Antony Tudor"), ("Jardin aux lilas", "Antony Tudor"),
    ("In the Upper Room", "Twyla Tharp"), ("The Green Table", "Kurt Jooss"), ("Revelations", "Alvin Ailey"),
    # — expansion saturation round 84 (2026-06-28 run autonome, maintenance) : chorégraphe UNIQUE moderne (gap-filtré) —
    ("Boléro (Béjart)", "Maurice Béjart"), ("La IXe Symphonie (Béjart)", "Maurice Béjart"), ("Le Jeune Homme et la Mort", "Roland Petit"),
    ("Carmen (Roland Petit)", "Roland Petit"), ("Notre-Dame de Paris (ballet)", "Roland Petit"), ("Push Comes to Shove", "Twyla Tharp"),
    ("Le Parc", "Angelin Preljocaj"), ("Blanche Neige (Preljocaj)", "Angelin Preljocaj"), ("Café Müller", "Pina Bausch"),
    ("Kontakthof", "Pina Bausch"), ("Nelken", "Pina Bausch"), ("Onegin", "John Cranko"), ("The Taming of the Shrew (Cranko)", "John Cranko"),
]


# ── PAYSAGISTE / CONCEPTEUR D'UN JARDIN-REPÈRE — l'art des jardins = œuvre attribuable (≠ l'édifice = architecte).
#    CANON concepteur UNIQUE certain ; jardins à intervenants multiples ÉCARTÉS (Stowe = Bridgeman+Kent+Brown,
#    Central Park = Olmsted+Vaux) -> FAUX=0. ────────────────────────────────────────────────────────────────────
JARDINS = [
    ("jardins de Versailles", "André Le Nôtre"), ("Vaux-le-Vicomte (jardins)", "André Le Nôtre"),
    ("jardins de Chantilly", "André Le Nôtre"), ("jardin des Tuileries", "André Le Nôtre"),
    ("parc de Sceaux", "André Le Nôtre"),
    ("Parc Güell", "Antoni Gaudí"),
    ("parc de Blenheim", "Capability Brown"), ("Croome Court", "Capability Brown"),
    ("jardin de Giverny", "Claude Monet"), ("Hidcote Manor Garden", "Lawrence Johnston"),
    ("jardin Majorelle", "Jacques Majorelle"), ("parc de la Villette", "Bernard Tschumi"),
    # — expansion saturation round 69 (2026-06-27 run autonome, maintenance) : concepteur unique de jardin/parc (gap-filtré) —
    ("Biltmore Estate (jardins)", "Frederick Law Olmsted"), ("Parc du Mont-Royal", "Frederick Law Olmsted"),
    ("Emerald Necklace", "Frederick Law Olmsted"), ("Parc Monceau", "Louis Carrogis Carmontelle"),
    ("Désert de Retz", "François Racine de Monville"), ("Parc des Buttes-Chaumont", "Jean-Charles Adolphe Alphand"),
    ("Bois de Boulogne", "Jean-Charles Adolphe Alphand"), ("Parc Montsouris", "Jean-Charles Adolphe Alphand"),
    # — expansion saturation round 87 (2026-06-28 run autonome, maintenance) : concepteur unique de jardin/parc (gap-filtré) —
    ("parc de Saint-Germain-en-Laye", "André Le Nôtre"), ("Stourhead", "Henry Hoare II"), ("Painshill Park", "Charles Hamilton"),
    ("Rousham House (jardins)", "William Kent"), ("Chiswick House (jardins)", "William Kent"), ("Crystal Palace Park", "Joseph Paxton"),
    ("Lurie Garden", "Piet Oudolf"), ("High Line (plantation)", "Piet Oudolf"),
]


# ── CRÉATEUR (DESIGNER) D'UN DRAPEAU — la conception graphique d'un drapeau est une œuvre attribuable (≠ la
#    donnée géo « pays -> drapeau » de T1). CANON designer UNIQUE documenté ; comités/attributions disputées
#    ÉCARTÉS (UE = Heitz/Lévy disputé, Brésil = Teixeira Mendes + Décio Villares) -> FAUX=0. ────────────────────
DRAPEAUX = [
    ("drapeau du Canada", "George F. G. Stanley"), ("drapeau de l'Inde", "Pingali Venkayya"),
    ("drapeau de l'Afrique du Sud", "Frederick Brownell"),
    ("drapeau de la fierté LGBT", "Gilbert Baker"), ("drapeau de la fierté transgenre", "Monica Helms"),
    ("drapeau du Nunavut", "Andrew Qappik"),
    # — expansion saturation round 70 (2026-06-27 run autonome, maintenance) : designer unique de drapeau (gap-filtré) —
    ("drapeau du Bangladesh", "Quamrul Hassan"), ("drapeau de l'Acadie", "Marcel-François Richard"),
    ("drapeau de la Terre", "John McConnell"), ("drapeau de Cascadia", "Alexander Baretich"),
    ("drapeau du Rwanda", "Alphonse Kirimobenecyo"), ("drapeau de la Barbade", "Grantley W. Prescod"),
    ("drapeau de la Dominique", "Alwin Bully"), ("drapeau de la fierté bisexuelle", "Michael Page"),
    ("drapeau de la fierté progressiste", "Daniel Quasar"), ("drapeau aborigène australien", "Harold Thomas"),
    # — expansion saturation round 88 (2026-06-28 run autonome, maintenance) : designer unique de drapeau (gap-filtré) —
    ("drapeau du Kazakhstan", "Shaken Niyazbekov"), ("drapeau du Guyana", "Whitney Smith"), ("drapeau de l'Antarctique", "Graham Bartram"),
    ("drapeau de Hong Kong", "Tao Ho"), ("drapeau de Chicago", "Wallace Rice"), ("drapeau de Washington D.C.", "Charles A. R. Dunn"),
    ("drapeau de l'Ohio", "John Eisenmann"), ("drapeau du Nouveau-Mexique", "Harry Mera"), ("drapeau de l'Alaska", "Benny Benson"),
]


# ── CRÉATEUR D'UN SYSTÈME D'ÉCRITURE / SCRIPT — invention d'un système graphique de notation (≠ langue construite
#    = conlang ; ≠ police = dessin typographique d'un alphabet existant). CANON inventeur UNIQUE certain ; duos
#    écartés (code Morse = Morse+Vail) -> FAUX=0. ──────────────────────────────────────────────────────────────
SYSTEMES_ECRITURE = [
    ("alphabet braille", "Louis Braille"), ("syllabaire cherokee", "Sequoyah"),
    ("hangeul", "Sejong le Grand"), ("alphabet shavien", "Ronald Kingsley Read"),
    ("tengwar", "J. R. R. Tolkien"), ("sténographie Pitman", "Isaac Pitman"),
    ("sténographie Gregg", "John Robert Gregg"), ("symboles Bliss", "Charles K. Bliss"),
    ("écriture Pollard", "Sam Pollard"),
    # — expansion saturation round 68 (2026-06-27 run autonome, maintenance) : système d'écriture à inventeur unique (gap-filtré) —
    ("alphabet Fraser", "James O. Fraser"), ("N'Ko", "Solomana Kanté"), ("syllabaire Vai", "Momolu Duwalu Bukele"),
    ("Ol Chiki", "Raghunath Murmu"), ("alphabet Osmanya", "Osman Yusuf Kenadid"), ("SignWriting", "Valerie Sutton"),
    ("Pinyin", "Zhou Youguang"),
    # — expansion saturation round 86 (2026-06-28 run autonome, maintenance) : système d'écriture à inventeur unique (gap-filtré) —
    ("alphabet arménien", "Mesrop Machtots"), ("alphabet glagolitique", "Cyrille"), ("Unifon", "John R. Malone"),
    ("Quikscript", "Ronald Kingsley Read"), ("sténographie Teeline", "James Hill"), ("sténographie Duployé", "Émile Duployé"),
    ("Speedwriting", "Emma Dearborn"), ("Cirth", "J. R. R. Tolkien"), ("Sarati", "J. R. R. Tolkien"),
    # — expansion saturation round 88 (2026-06-28 run autonome, maintenance) : système d'écriture à inventeur unique (gap-filtré) —
    ("écriture Soyombo", "Zanabazar"), ("mandombe", "Wabeladio Payi"), ("alphabet Bamoun", "Ibrahim Njoya"),
    ("alphabet Mende", "Kisimi Kamara"), ("Pahawh Hmong", "Shong Lue Yang"),
]


# ── CHORÉGRAPHE D'UNE COMÉDIE MUSICALE — complète l'équipe créative (compositeur/parolier/librettiste déjà faits)
#    de la comédie musicale ; la chorégraphie est une œuvre attribuable. CANON chorégraphe UNIQUE de la production
#    originale ; revivals/co-chorégraphies ambigus écartés -> FAUX=0. DISTINCT de choregraphe_ballet. ──────────────
CHOREGRAPHES_MUSICAL = [
    ("West Side Story", "Jerome Robbins"), ("Fiddler on the Roof", "Jerome Robbins"),
    ("Chicago", "Bob Fosse"), ("Sweet Charity", "Bob Fosse"), ("Pippin", "Bob Fosse"),
    ("Oklahoma!", "Agnes de Mille"), ("Carousel", "Agnes de Mille"),
    ("A Chorus Line", "Michael Bennett"),
    ("Hello, Dolly!", "Gower Champion"), ("42nd Street", "Gower Champion"),
    ("The Producers", "Susan Stroman"), ("Contact", "Susan Stroman"),
    ("Cats", "Gillian Lynne"),
    ("Hamilton", "Andy Blankenbuehler"), ("In the Heights", "Andy Blankenbuehler"),
    ("Newsies", "Christopher Gattelli"),
    # — expansion saturation round 67 (2026-06-27 run autonome, maintenance) : chorégraphe UNIQUE de comédie musicale (gap-filtré) —
    ("On the Town", "Jerome Robbins"), ("Gypsy", "Jerome Robbins"), ("High Button Shoes", "Jerome Robbins"),
    ("Damn Yankees", "Bob Fosse"), ("The Pajama Game", "Bob Fosse"), ("Dancin'", "Bob Fosse"),
    ("Brigadoon", "Agnes de Mille"), ("Paint Your Wagon", "Agnes de Mille"), ("Dreamgirls", "Michael Bennett"),
    ("Crazy for You", "Susan Stroman"), ("Movin' Out", "Twyla Tharp"), ("Bandstand", "Andy Blankenbuehler"),
    # — expansion saturation round 85 (2026-06-28 run autonome, maintenance) : chorégraphe UNIQUE Broadway moderne (gap-filtré) —
    ("The Phantom of the Opera", "Gillian Lynne"), ("Kinky Boots", "Jerry Mitchell"), ("Hairspray", "Jerry Mitchell"),
    ("Legally Blonde", "Jerry Mitchell"), ("Spamalot", "Casey Nicholaw"), ("The Book of Mormon", "Casey Nicholaw"),
    ("Aladdin", "Casey Nicholaw"), ("Something Rotten!", "Casey Nicholaw"), ("Memphis", "Sergio Trujillo"),
    ("Jersey Boys", "Sergio Trujillo"), ("Ain't Too Proud", "Sergio Trujillo"), ("Bring in 'da Noise, Bring in 'da Funk", "Savion Glover"),
    ("Fela!", "Bill T. Jones"), ("Spring Awakening", "Bill T. Jones"), ("Billy Elliot the Musical", "Peter Darling"),
    ("Matilda the Musical", "Peter Darling"), ("An American in Paris", "Christopher Wheeldon"), ("Anything Goes", "Kathleen Marshall"),
]


# ── COMPOSITEUR D'OPÉRETTE — genre distinct de l'opéra (compositeur_opera) ; compositeur UNIQUE certain.
#    Titres d'opérette (≠ opéra) seulement -> pas de redondance avec OPERAS. FAUX=0. ──────────────────────────────
OPERETTES = [
    ("Orphée aux enfers", "Jacques Offenbach"), ("La Belle Hélène", "Jacques Offenbach"),
    ("La Vie parisienne", "Jacques Offenbach"), ("La Grande-Duchesse de Gérolstein", "Jacques Offenbach"),
    ("La Périchole", "Jacques Offenbach"),
    ("La Chauve-Souris", "Johann Strauss II"), ("Le Baron tzigane", "Johann Strauss II"),
    ("Une nuit à Venise", "Johann Strauss II"),
    ("La Veuve joyeuse", "Franz Lehár"), ("Le Pays du sourire", "Franz Lehár"),
    ("Le Comte de Luxembourg", "Franz Lehár"),
    ("The Mikado", "Arthur Sullivan"), ("HMS Pinafore", "Arthur Sullivan"),
    ("The Pirates of Penzance", "Arthur Sullivan"), ("The Gondoliers", "Arthur Sullivan"),
    ("Iolanthe", "Arthur Sullivan"),
    ("La Princesse Csardas", "Emmerich Kálmán"), ("Comtesse Maritza", "Emmerich Kálmán"),
    ("Le Soldat de chocolat", "Oscar Straus"),
    ("Véronique", "André Messager"), ("La Fille de Madame Angot", "Charles Lecocq"),
    # — expansion saturation round 65 (2026-06-27 run autonome, maintenance) : compositeur unique d'opérette (gap-filtré) —
    ("Les Brigands", "Jacques Offenbach"), ("Barbe-Bleue", "Jacques Offenbach"), ("La Fille du tambour-major", "Jacques Offenbach"),
    ("Le Tsarévitch", "Franz Lehár"), ("Giuditta", "Franz Lehár"), ("Patience", "Arthur Sullivan"),
    ("Ruddigore", "Arthur Sullivan"), ("The Yeomen of the Guard", "Arthur Sullivan"), ("Princess Ida", "Arthur Sullivan"),
    ("Trial by Jury", "Arthur Sullivan"), ("Les P'tites Michu", "André Messager"), ("Monsieur Beaucaire", "André Messager"),
    ("Le Petit Duc", "Charles Lecocq"), ("Mam'zelle Nitouche", "Hervé"), ("Les Cloches de Corneville", "Robert Planquette"),
    ("La Mascotte", "Edmond Audran"), ("Rêve de valse", "Oscar Straus"),
    # — expansion saturation round 82 (2026-06-28 run autonome, maintenance) : compositeur unique d'opérette (gap-filtré) —
    ("Geneviève de Brabant", "Jacques Offenbach"), ("Madame Favart", "Jacques Offenbach"), ("Eva", "Franz Lehár"),
    ("Paganini", "Franz Lehár"), ("La Princesse du cirque", "Emmerich Kálmán"), ("Utopia, Limited", "Arthur Sullivan"),
    ("The Grand Duke", "Arthur Sullivan"), ("La Poupée", "Edmond Audran"), ("Miss Helyett", "Edmond Audran"),
    ("Fortunio", "André Messager"), ("Le Petit Faust", "Hervé"), ("La Belle Galathée", "Franz von Suppé"),
    ("Boccace", "Franz von Suppé"), ("Der Bettelstudent", "Carl Millöcker"), ("Der Vogelhändler", "Carl Zeller"),
]


# ── COMPOSITEUR D'ORATORIO — Wikidata FR ~0 entité (Q187947) -> voie canon. Compositeur UNIQUE certain ; genre
#    distinct (oratorio/légende dramatique). Titres d'oratorio seulement. FAUX=0. ──────────────────────────────────
ORATORIOS = [
    ("Le Messie", "Georg Friedrich Haendel"), ("Israël en Égypte", "Georg Friedrich Haendel"),
    ("Judas Maccabée", "Georg Friedrich Haendel"), ("Samson (oratorio)", "Georg Friedrich Haendel"),
    ("Salomon (oratorio)", "Georg Friedrich Haendel"),
    ("La Création", "Joseph Haydn"), ("Les Saisons (oratorio)", "Joseph Haydn"),
    ("Elias", "Felix Mendelssohn"), ("Paulus", "Felix Mendelssohn"),
    ("L'Enfance du Christ", "Hector Berlioz"),
    ("Le Roi David", "Arthur Honegger"), ("Jeanne au bûcher", "Arthur Honegger"),
    ("The Dream of Gerontius", "Edward Elgar"), ("Belshazzar's Feast", "William Walton"),
    ("A Child of Our Time", "Michael Tippett"),
    # — expansion saturation round 66 (2026-06-27 run autonome, maintenance) : compositeur unique d'oratorio (gap-filtré) —
    ("Oratorio de Noël", "Jean-Sébastien Bach"), ("Oratorio de Pâques", "Jean-Sébastien Bach"),
    ("Passion selon saint Matthieu", "Jean-Sébastien Bach"), ("Les Sept Dernières Paroles du Christ", "Joseph Haydn"),
    ("Saul", "Georg Friedrich Haendel"), ("Theodora", "Georg Friedrich Haendel"), ("Jephtha", "Georg Friedrich Haendel"),
    ("Esther", "Georg Friedrich Haendel"), ("The Apostles", "Edward Elgar"), ("The Kingdom", "Edward Elgar"),
    ("Les Béatitudes", "César Franck"), ("Oedipus Rex", "Igor Stravinsky"),
    # — expansion saturation round 83 (2026-06-28 run autonome, maintenance) : compositeur unique d'oratorio (gap-filtré) —
    ("Christus (Liszt)", "Franz Liszt"), ("La Légende de sainte Élisabeth", "Franz Liszt"), ("Stabat Mater (Dvořák)", "Antonín Dvořák"),
    ("Sainte Ludmila", "Antonín Dvořák"), ("Rédemption", "César Franck"), ("Le Paradis et la Péri", "Robert Schumann"),
    ("Sancta Civitas", "Ralph Vaughan Williams"), ("Dona Nobis Pacem", "Ralph Vaughan Williams"), ("La Passion selon saint Luc", "Krzysztof Penderecki"),
    ("Gurre-Lieder", "Arnold Schönberg"), ("The Mask of Time", "Michael Tippett"), ("Une cantate de Noël", "Arthur Honegger"),
]


# ── COMPOSITEUR DE REQUIEM — genre distinct (messe des morts) ; compositeur UNIQUE certain. Titres qualifiés par
#    le compositeur (beaucoup de « Requiem » homonymes). FAUX=0. ───────────────────────────────────────────────────
REQUIEMS = [
    ("Requiem de Mozart", "Wolfgang Amadeus Mozart"), ("Requiem de Verdi", "Giuseppe Verdi"),
    ("Requiem de Fauré", "Gabriel Fauré"), ("Un requiem allemand", "Johannes Brahms"),
    ("Grande messe des morts", "Hector Berlioz"), ("Requiem de Dvořák", "Antonín Dvořák"),
    ("Requiem de Duruflé", "Maurice Duruflé"), ("War Requiem", "Benjamin Britten"),
    ("Requiem de Ligeti", "György Ligeti"), ("Requiem polonais", "Krzysztof Penderecki"),
    ("Requiem de Cherubini", "Luigi Cherubini"), ("Requiem de Saint-Saëns", "Camille Saint-Saëns"),
    # — expansion saturation round 66 (2026-06-27 run autonome, maintenance) : compositeur unique de requiem (gap-filtré) —
    ("Requiem de Rutter", "John Rutter"), ("Requiem de Lloyd Webber", "Andrew Lloyd Webber"),
    ("Requiem de Howells", "Herbert Howells"), ("Requiem de Pizzetti", "Ildebrando Pizzetti"),
    ("Requiem de Liszt", "Franz Liszt"), ("Requiem de Bruckner", "Anton Bruckner"),
    ("Messe de Requiem (Gossec)", "François-Joseph Gossec"),
    # — expansion saturation round 83 (2026-06-28 run autonome, maintenance) : compositeur unique de requiem (gap-filtré) —
    ("Requiem de Schnittke", "Alfred Schnittke"), ("Requiem de Reger", "Max Reger"), ("The Armed Man", "Karl Jenkins"),
    ("Requiem de Rheinberger", "Josef Rheinberger"), ("Requiem de Donizetti", "Gaetano Donizetti"), ("Requiem de Suppé", "Franz von Suppé"),
]


# ── COMPOSITEUR DE ZARZUELA — genre lyrique espagnol distinct (≠ opéra/opérette) ; compositeur UNIQUE certain ;
#    duos écartés (La Gran Vía = Chueca+Valverde, La leyenda del beso = Soutullo+Vert). FAUX=0. ───────────────────
ZARZUELAS = [
    ("La verbena de la Paloma", "Tomás Bretón"), ("Doña Francisquita", "Amadeo Vives"), ("Bohemios", "Amadeo Vives"),
    ("Luisa Fernanda", "Federico Moreno Torroba"), ("La revoltosa", "Ruperto Chapí"),
    ("La del manojo de rosas", "Pablo Sorozábal"), ("La tabernera del puerto", "Pablo Sorozábal"),
    ("Katiuska", "Pablo Sorozábal"), ("El barberillo de Lavapiés", "Francisco Asenjo Barbieri"),
    ("Pan y toros", "Francisco Asenjo Barbieri"), ("Agua, azucarillos y aguardiente", "Federico Chueca"),
    ("La canción del olvido", "José Serrano"), ("El caserío", "Jesús Guridi"),
    # — expansion saturation round 89 (2026-06-28 run autonome, maintenance) : compositeur unique de zarzuela (gap-filtré) —
    ("La alegría de la huerta", "Federico Chueca"), ("El bateo", "Federico Chueca"), ("La corte de Faraón", "Vicente Lleó"),
    ("Las golondrinas", "José María Usandizaga"), ("El huésped del Sevillano", "Jacinto Guerrero"), ("Los gavilanes", "Jacinto Guerrero"),
    ("La rosa del azafrán", "Jacinto Guerrero"), ("La Dolores", "Tomás Bretón"), ("Molinos de viento", "Pablo Luna"),
    ("El asombro de Damasco", "Pablo Luna"), ("Maruxa", "Amadeo Vives"), ("La Generala", "Amadeo Vives"),
    ("El rey que rabió", "Ruperto Chapí"), ("La bruja", "Ruperto Chapí"), ("El puñao de rosas", "Ruperto Chapí"),
    ("Curro Vargas", "Ruperto Chapí"), ("Black, el payaso", "Pablo Sorozábal"),
]


def main():
    print("== CANON T5 depuis connaissance modèle (offline, FAUX=0 : canon indiscutable seulement) ==")
    publie("compositeur_opera", "convention",
           SRC + " — compositeur d'opéra (répertoire canonique)", OPERAS)
    publie("compositeur_comedie_musicale", "convention",
           SRC + " — compositeur de comédie musicale (« music by » canonique)", MUSICALS)
    publie("compositeur_ballet", "convention",
           SRC + " — compositeur de ballet (répertoire canonique)", BALLETS)
    publie("librettiste_opera", "convention",
           SRC + " — librettiste d'opéra (librettiste unique certain)", LIBRETTISTES_OPERA)
    publie("parolier_comedie_musicale", "convention",
           SRC + " — parolier de comédie musicale (parolier unique certain)", PAROLIERS_MUSICAL)
    publie("auteur_jeu_societe", "convention",
           SRC + " — auteur de jeu de société (designer unique certain)", JEUX_SOCIETE)
    publie("createur_police_ecriture", "convention",
           "connaissance modèle (Claude) — canon haute-confiance (Wikidata FR sous-peuplée : "
           "police d'écriture Q17489160 = 0 entité au 2026-06-26) — créateur (type designer) unique "
           "certain, co-créations écartées", POLICES)
    publie("createur_langage_programmation", "convention",
           "connaissance modèle (Claude) — canon haute-confiance (Wikidata FR sparse/bruitée : "
           "Q9143 ~34-149 entités, fonc 85 % = équipes) — créateur unique incontesté, duos/équipes écartés",
           LANGAGES)
    publie("createur_serie_television", "convention",
           "connaissance modèle (Claude) — canon haute-confiance (Wikidata `createur_serie` P170 rejeté : "
           "ratio 0.73 fonc 86 %) — créateur/showrunner unique incontesté, duos/équipes écartés", SERIES_TV)
    publie("createur_logiciel", "convention",
           "connaissance modèle (Claude) — canon haute-confiance — créateur unique incontesté d'un logiciel "
           "emblématique (jeux exclus -> concepteur_jeu ; duos/équipes écartés)", LOGICIELS)
    publie("librettiste_comedie_musicale", "convention",
           "connaissance modèle (Claude) — canon haute-confiance — auteur du livret (« book ») de comédie "
           "musicale, auteur unique certain (duos/équipes écartés), distinct du parolier et du compositeur",
           LIBRETTISTES_MUSICAL)
    publie("inventeur_instrument_musique", "convention",
           "connaissance modèle (Claude) — canon haute-confiance — inventeur UNIQUE indiscutable d'un type "
           "d'instrument de musique (disputés/duos écartés ; distinct de la facture instrumentale = fabricants)",
           INSTRUMENTS_INVENTEUR)
    publie("parfumeur_parfum", "convention",
           "connaissance modèle (Claude) — canon haute-confiance (histoire de la parfumerie) — parfumeur "
           "(« nez ») UNIQUE certain d'un parfum, attribution établie ; duos écartés",
           PARFUMS)
    publie("auteur_jeu_role", "convention",
           "connaissance modèle (Claude) — canon haute-confiance — auteur/créateur UNIQUE certain d'un jeu de "
           "rôle sur table (équipes/duos écartés ; distinct de auteur_jeu_societe et concepteur_jeu)",
           JEUX_ROLE)
    publie("createur_objet_design", "convention",
           "connaissance modèle (Claude) — canon haute-confiance — créateur (designer) UNIQUE certain d'un objet "
           "de design iconique (mobilier/luminaire) ; duos écartés (Eames, Castiglioni) ; Barcelona écartée (doute)",
           OBJETS_DESIGN)
    publie("createur_langue_construite", "convention",
           SRC + " — créateur UNIQUE certain d'une langue construite (conlang) ; équipes/duos/réformes écartés "
           "(Ido, Interlingua, Lojban) ; DISTINCT des langages de programmation",
           LANGUES_CONSTRUITES)
    publie("createur_logo", "convention",
           SRC + " — designer UNIQUE certain d'un logo iconique ; agences/équipes écartées",
           LOGOS)
    publie("choregraphe_ballet", "convention",
           SRC + " — chorégraphe UNIQUE de la création/version-repère d'un ballet ; duos et revivals ambigus "
           "écartés ; DISTINCT du compositeur du ballet",
           CHOREGRAPHIES)
    publie("paysagiste_jardin", "convention",
           SRC + " — concepteur/paysagiste UNIQUE certain d'un jardin ou parc-repère ; jardins à intervenants "
           "multiples écartés ; DISTINCT de l'architecte de l'édifice",
           JARDINS)
    publie("createur_drapeau", "convention",
           SRC + " — designer UNIQUE documenté d'un drapeau ; comités/attributions disputées écartés ; "
           "DISTINCT de la donnée géographique pays→drapeau",
           DRAPEAUX)
    publie("createur_systeme_ecriture", "convention",
           SRC + " — inventeur UNIQUE certain d'un système d'écriture/script ; duos écartés (Morse) ; "
           "DISTINCT d'une langue construite (conlang) et d'une police (typographie)",
           SYSTEMES_ECRITURE)
    publie("choregraphe_comedie_musicale", "convention",
           SRC + " — chorégraphe UNIQUE de la production originale d'une comédie musicale ; revivals/"
           "co-chorégraphies ambigus écartés ; DISTINCT de choregraphe_ballet",
           CHOREGRAPHES_MUSICAL)
    publie("compositeur_operette", "convention",
           SRC + " — compositeur UNIQUE d'une opérette (genre distinct de l'opéra) ; titres d'opérette seulement",
           OPERETTES)
    publie("compositeur_oratorio", "convention",
           SRC + " — compositeur UNIQUE d'un oratorio (genre distinct) ; titres d'oratorio seulement",
           ORATORIOS)
    publie("compositeur_requiem", "convention",
           SRC + " — compositeur UNIQUE d'un requiem (messe des morts) ; titres qualifiés par le compositeur",
           REQUIEMS)
    publie("compositeur_zarzuela", "convention",
           SRC + " — compositeur UNIQUE d'une zarzuela (genre lyrique espagnol distinct) ; duos écartés",
           ZARZUELAS)


if __name__ == "__main__":
    main()
