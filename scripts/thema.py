#!/usr/bin/env python3
"""Alles Themenspezifische der taeglichen Studienauswahl — und sonst nichts.

Diese Datei ist die EINZIGE unter scripts/, die sich von Portal zu Portal
inhaltlich unterscheidet. `update_studies.py` bleibt in allen Portalen
wortgleich und importiert von hier. Wer die Auswahl aendern will, aendert
Text in dieser Datei — keinen Code.

Erzeugt von neues-portal.py aus dem Themenprofil `themen/pflege.json`.
Weiterentwickelt wird danach hier, nicht im Profil.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------- Kennungen
# NCBI bittet bei automatisierten Zugriffen um eine Tool-Kennung.
NCBI_TOOL = "pflege-portal"

# ----------------------------------------------------------- Die Suchabfrage
# Zwei Bloecke, die BEIDE zutreffen muessen. Ohne den zweiten spuelt die Abfrage
# Arbeiten herein, die das Thema nur streifen; ohne den ersten kommt beliebige
# Versorgungsliteratur.
#
# Zur Feldwahl: [MeSH Terms] fasst breit, [Majr] verlangt das Haupt-Schlagwort,
# [Title/Abstract] fasst am breitesten, [Title] am engsten. Faustregel aus den
# Schwesterportalen: Steht ein Begriff in fremden Abstracts als blosses Werkzeug
# oder Beiwerk, ist [Title/Abstract] untauglich — dann [Majr]/[Title]. Im
# KI-Portal sank die Trefferzahl dadurch von 605.000 auf 321.000, und erst die
# kleinere Menge handelte tatsaechlich vom Thema.
#
# Vor dem Livegang die Trefferzahl in PubMed nachsehen und hier notieren, damit
# spaetere Aenderungen messbar bleiben.
_THEMA = (
    '(("Nursing Care"[Majr] OR "Nursing"[Majr] OR "Long-Term Care"[Majr] '
    'OR "Nursing Homes"[Majr] OR "Homes for the Aged"[Majr] '
    'OR "Home Care Services"[Majr] OR "Home Nursing"[Majr] '
    'OR "Caregivers"[Majr] OR "Caregiver Burden"[Majr] '
    'OR "Nursing Staff"[Majr] OR "Nurses"[Majr] OR "Geriatric Nursing"[Majr] '
    'OR "Nursing Assistants"[Majr] OR "Assisted Living Facilities"[Majr] '
    'OR "Skilled Nursing Facilities"[Majr] OR "Nursing Process"[Majr] '
    'OR "Nursing Research"[Majr] OR "Nursing Evaluation Research"[Majr] '
    'OR "Nurse\'s Role"[Majr] OR "Nurse-Patient Relations"[Majr]) '
    'OR (nursing[Title] OR nurse*[Title] OR "long-term care"[Title] '
    'OR "nursing home*"[Title] OR "residential care"[Title] '
    'OR "aged care"[Title] OR caregiver*[Title] OR "care home*"[Title] '
    'OR "home care"[Title] OR "informal care*"[Title] '
    'OR "care worker*"[Title] OR "care dependency"[Title]))'
)
_KONTEXT = (
    '("Delivery of Health Care"[MeSH Terms] OR "Health Services"[MeSH Terms] '
    'OR "Quality of Health Care"[MeSH Terms] OR "Patient Care"[MeSH Terms] '
    'OR "Health Policy"[MeSH Terms] OR "Patient Safety"[MeSH Terms] '
    'OR "Health Workforce"[MeSH Terms] OR "Quality of Life"[MeSH Terms] '
    'OR "health care"[Title/Abstract] OR "health services"[Title/Abstract] '
    'OR "quality of care"[Title/Abstract] OR "patient outcome*"[Title/Abstract] '
    'OR workload[Title/Abstract] OR staffing[Title/Abstract] '
    'OR implementation[Title/Abstract] OR residents[Title/Abstract] '
    'OR patients[Title/Abstract] OR "care quality"[Title/Abstract])'
)
# "Humans"[MeSH] haelt Tier-, Labor- und reine Modellarbeiten heraus.
TERM = os.environ.get(
    "SEARCH_TERM",
    f'(({_THEMA} AND {_KONTEXT}) AND "Humans"[MeSH Terms])',
)
# Zweite Abfrage, damit Arbeiten mit Deutschland- und Europabezug den
# Kandidatenpool sicher erreichen. Ueber MeSH und Autorenadresse, nicht ueber
# Journalnamen - deutschsprachige Journale liefern kaum Treffer.
TERM_DE = os.environ.get(
    "SEARCH_TERM_DE",
    f"{TERM} AND (Germany[MeSH Terms] OR Germany[Affiliation] "
    "OR Europe[MeSH Terms] OR Europe[Affiliation])",
)

# Groesse des Kandidatenpools. Europa steht vorn und stellt die Mehrheit -
# ein Sprachmodell gewichtet, was es zuerst liest. Wer das umdreht, bekommt
# eine Auswahl ohne Bezug zu hiesigen Verhaeltnissen; im Klima-Portal ist
# genau das passiert.
POOL_EUROPA = 30
POOL_ALLGEMEIN = 25
# Welche Abfrage vorn steht. True ist der Regelfall und die Lehre aus dem
# Klima-Portal: Steht die allgemeine Abfrage vorn, kommt eine Auswahl ohne
# Bezug zu hiesigen Verhaeltnissen heraus. Das Versorgungsforschungs-Portal
# arbeitet historisch andersherum (40 allgemein + 15 deutsch) - dort steht
# hier False, damit der Anschluss an die Vorlage nichts an seiner taeglichen
# Auswahl geaendert hat. Umstellen ist eine redaktionelle Entscheidung.
EUROPA_ZUERST = True

# Wie viele Studien taeglich erscheinen. SOLL wird im Prompt verlangt und beim
# Kappen verwendet; ueber MAX wird gekappt, unter MIN bricht der Lauf ab.
# **Nicht ins JSON-Schema schreiben** - die Anthropic-API lehnt minItems > 1
# und maxItems ab (am 17.08.2026 zweimal mit HTTP 400 belegt).
ANZAHL_SOLL = 6
ANZAHL_MAX = 7
ANZAHL_MIN = 1
# True: zu viele Studien werden auf ANZAHL_SOLL gekuerzt (die Auswahl ist nach
# Relevanz geordnet, die vorderen sind brauchbar). False: zu viele lassen den
# Lauf scheitern - so hielt es das Versorgungsforschungs-Portal von Anfang an.
KAPPEN = True

# ------------------------------------------------------------------- Prompts
SYSTEM = (
    "Du bist Fachredakteur fuer Pflege und Langzeitversorgung. Aus einer "
    "Liste von PubMed-Abstracts waehlst du die relevantesten aktuellen "
    "Studien aus und fasst sie praezise auf Deutsch zusammen. Deine "
    "Leserschaft arbeitet im deutschen Pflegewesen: Pflegemanagement, "
    "Einrichtungstraeger, Pflegekammern, Kostentraeger, Selbstverwaltung, "
    "Pflegewissenschaft und Gesundheitspolitik. Sie will wissen, was eine "
    "Massnahme in der Versorgung bewirkt - fuer Pflegebeduerftige wie fuer "
    "die Pflegenden -, nicht welches Instrument die beste Guetekennzahl hat."
)

USER_TEMPLATE = """Unten stehen aktuelle PubMed-Abstracts (nach Datum sortiert).

Waehle GENAU 6 Studien aus, die (a) die pflegerische Versorgung, die Langzeitpflege oder die Situation der Pflegenden untersuchen UND (b) im
Abstract ein BENENNBARES ERGEBNIS berichten. Bei quantitativen Arbeiten heisst
das: konkrete Zahlen (Prozentwerte, Effektstaerken, Odds/Hazard Ratios, Zeit-
oder Kostenwirkungen, Fallzahlen, p-Werte) - und die gehoeren dann auch in die
Zusammenfassung. Qualitative Studien (Interviews, Fokusgruppen) und
Expertenpapiere sind ausdruecklich zugelassen; bei ihnen tritt an die Stelle
der Zahl die klar benannte Kernaussage - welche Faktoren, welche Bedingungen,
welche Empfehlung. Was NICHT genuegt, ist ein Abstract, der nur ankuendigt,
was untersucht wurde, ohne zu sagen, was dabei herauskam.
Ueberspringe Studien ohne Abstract oder ohne benennbares Ergebnis. Achte auf
thematische Vielfalt und mische quantitative und qualitative Arbeiten.

THEMATISCHE RANGFOLGE - in dieser Reihenfolge bevorzugen:
  1. Versorgung und Ergebnis: Massnahmen in Pflegeheim, ambulantem Dienst
     oder Klinik mit gemessener Wirkung auf Pflegebeduerftige - Dekubitus,
     Stuerze, Ernaehrung, Schmerz, Mobilitaet, Krankenhauseinweisungen,
     Lebensqualitaet, Selbstbestimmung.
  2. Personal und Arbeitsbedingungen: Personalbemessung, Qualifikationsmix,
     Arbeitsbelastung, Verbleib im Beruf, unterlassene Pflege, neue
     Aufgabenzuschnitte - jeweils mit belegtem Zusammenhang zu Ergebnis
     oder Verweildauer im Beruf.
  3. System und Steuerung: Finanzierung und Eigenanteile, Qualitaetspruefung
     und Qualitaetsindikatoren, sektorenuebergreifende Versorgung,
     Entlassmanagement, kommunale Pflegeplanung, Pflegepolitik.
  4. Pflegende Angehoerige und haeusliche Versorgung: Belastung, Entlastungs-
     angebote, Vereinbarkeit von Pflege und Beruf, Pflegearrangements.
  5. Demenz, Palliativversorgung und Versorgung am Lebensende, sofern
     pflegerisch und nicht rein medikamentoes.

NICHT in die Auswahl gehoeren:
reine Instrumentenentwicklung und Fragebogenvalidierung ohne Anwendung in der
Versorgung, Querschnittsbefragungen ohne Bezugsgroesse ("X Prozent der
Befragten fuehlen sich belastet"), Arbeiten, die Pflegekraefte nur als
Stichprobe fuer eine ganz andere Fragestellung verwenden, medikamentoese
Studien mit pflegerischem Anstrich, Uebersichten, die nichts Eigenes berichten sowie
Einzelfallberichte und Erfahrungsberichte einzelner Einrichtungen.

HARTE REGELN ZUR ZUSAMMENSETZUNG (sie gehen der thematischen Rangfolge vor):
  1. MINDESTENS DREI der sechs Studien muessen aus Europa stammen oder ein
     europaeisches Pflegesystem betreffen. Liegen weniger als drei solche
     Arbeiten vor, nimm die verbleibenden Plaetze aus dem Rest - aber
     schoepfe die europaeischen zuerst aus.
  2. HOECHSTENS ZWEI der sechs duerfen sich auf die Akutpflege im Krankenhaus
     beziehen. Die Klinikpflege publiziert um ein Vielfaches mehr als die
     Langzeit- und die haeusliche Pflege und wuerde die Auswahl sonst allein
     bestreiten - waehrend die Mehrheit der Pflegebeduerftigen zu Hause oder
     im Heim versorgt wird.
  3. HOECHSTENS EINE darf ausschliesslich die Perspektive der Pflegenden
     erheben, ohne ein Ergebnis fuer die Versorgten zu berichten.

ZWEITES AUSWAHLKRITERIUM - Übertragbarkeit auf Deutschland:
Bei sonst gleicher Qualität hat die übertragbare Studie IMMER Vorrang vor der
aktuelleren.

  Hoch:    Deutschland und deutschsprachiger Raum, vergleichbare Sozial-
           versicherungssysteme.
  Mittel:  Übriges Europa, Kanada, Australien - andere Ausgangslage,
           ähnlicher Versorgungsauftrag.
  Gering:  USA und Länder mit grundlegend anderer Finanzierung oder
           Ressourcenlage. Nur nehmen, wenn die Fragestellung davon
           unabhängig ist.

Besonderheit dieses Themenfeldes: Pflege ist staerker als jedes andere
Versorgungsfeld an nationales Recht und Berufsstruktur gebunden. Massgeblich
sind drei Unterschiede, die bei jeder Studie mitgedacht werden muessen:
  - Finanzierung: Deutschland, Oesterreich, Japan und die Niederlande haben
    eine eigene Pflegeversicherung mit Teilkasko-Logik; Grossbritannien,
    Skandinavien und Italien finanzieren steuerbasiert und beduerftigkeits-
    geprueft. Aussagen zu Eigenanteilen und Leistungsanspruechen sind
    zwischen diesen Welten NICHT uebertragbar.
  - Qualifikation: Die dreijaehrige generalistische Pflegeausbildung
    hierzulande entspricht nicht der akademischen Registered Nurse im
    angelsaechsischen Raum. Studien zu erweiterten Kompetenzen (Advanced
    Nursing Practice, Verordnungsrechte) beschreiben deshalb oft etwas, das
    es in Deutschland rechtlich gar nicht gibt - das gehoert in transfer.
  - Versorgungsform: US-amerikanische Skilled Nursing Facilities sind
    kurzzeitige Nachsorgeeinrichtungen, keine Pflegeheime im hiesigen Sinn.

Fuer jede Studie:
- journal: Journalname genau so, wie er in der Kopfzeile des Abstracts steht -
  Abkuerzung nicht aufloesen, nichts ergaenzen. (Wird ohnehin durch die Angabe
  aus PubMed ersetzt; rate hier nichts.)
- year: Erscheinungsjahr, z. B. "2026"
- pmid: die PubMed-ID
- title: praegnanter deutscher Titel, **hoechstens 160 Zeichen**. Der
  Torwaechter lehnt alles ueber 200 Zeichen ab und stoppt damit die ganze
  Ausgabe - Methode und Population gehoeren nicht in den Titel, sie stehen
  in sum und transfer.
  **Er MUSS mit der pflegerischen bzw. versorgungsbezogenen Fragestellung
  beginnen; die einzelne Diagnose steht hinten oder gar nicht drin.**
  Viele Arbeiten in diesem Feld haengen an einem klinischen Anlassfall -
  Sturz, Dekubitus, Delir -, und die Abstracts sind danach betitelt. Wer das
  uebernimmt, macht aus dem Portal eine beliebige medizinische
  Studiensammlung statt eines Pflegeportals.
  Gut:      "Mehr Fachkraefte je Bewohner, weniger Krankenhauseinweisungen:
             was eine Personalaufstockung in 240 Heimen bewirkt hat"
            "Entlastungsangebote fuer pflegende Angehoerige: was sie an
             Belastung nehmen - und was nicht"
  Schlecht: "Praevalenz von Dekubitus bei Heimbewohnern" (fuehrt mit der
             Diagnose, die Versorgungsfrage verschwindet)
- sum: 1 Satz auf Deutsch, was die Studie untersucht hat. Wenn der genannte
  Anlassfall nur das Material ist, an dem gerechnet wurde, sage das
  ausdruecklich - sonst haelt die Leserschaft ihn fuer den Gegenstand.
- result: Deutsch, die konkreten Zahlen/Befunde + ein kurzer Einordnungssatz.
  Deutsches Zahlenformat mit Komma (z. B. 0,63). **Der Einordnungssatz darf
  nicht behaupten, was die Autoren selbst ablehnen.** Wo ein Abstract eine
  Deutung ausdruecklich zurueckweist, diese Einschraenkung uebernehmen statt
  sie zu ueberschreiben. Ein Rechercheportal referiert, es wertet nicht auf.
- transfer: EIN Halbsatz (höchstens 12 Wörter), warum das Ergebnis für Deutschland
  taugt - oder wo die Grenze liegt. Nenne Land bzw. System und Datengrundlage.
  Keine ganzen Sätze, keine Wiederholung des Titels.
  Gut:      "Deutsche Klinikdaten, vergleichbare Dokumentationspflichten"
            "Niederlande, vergleichbares Versicherungssystem"
            "USA - nur der Sicherheitsbefund ist übertragbar"
  Schlecht: "Diese Studie ist gut übertragbar." (sagt nichts)

WICHTIG - Fachterminologie: Etablierte englische Fachbegriffe NICHT eindeutschen.
Sie sind auch im deutschen Fachdeutsch stehende Begriffe; eine woertliche
Uebersetzung wirkt unprofessionell und erschwert das Wiederfinden.
Beispiele fuer Begriffe, die englisch bleiben: Skill Mix, Case Management,
Advanced Nursing Practice, Screening, Assessment, Follow-up, Outcome,
Baseline, Setting, Hazard Ratio, Odds Ratio, Public Health.
Deutsche Fachbegriffe, die es gibt, aber unbedingt verwenden:
Pflegebeduerftigkeit, Pflegegrad, Personalbemessung, Qualifikationsmix,
Expertenstandard, Dekubitusprophylaxe, Entlassmanagement, Eigenanteil,
pflegende Angehoerige, Verhinderungspflege, freiheitsentziehende Massnahmen.
**Nicht eindeutschen und nicht verwechseln:** "nursing home" ist das
Pflegeheim, "skilled nursing facility" dagegen eine US-Nachsorgeeinrichtung -
wo der Unterschied traegt, gehoert er in einen Halbsatz.
Faustregel: Wuerde eine deutsche Fachzeitschrift wie Monitor Versorgungsforschung
den Begriff englisch stehen lassen, dann tue es auch. Im Zweifel englisch
belassen und bei Bedarf eine kurze deutsche Erlaeuterung in Klammern ergaenzen.

Gib ausschliesslich das geforderte JSON zurueck.

=== ABSTRACTS ===
{abstracts}
"""
