Entscheidungsdokumentation - Gruppe A2 

Kurzbeschreibung

Ein Peer-to-Peer-Chatprogramm, das es ermöglicht, Textnachrichten und Bilder zwischen Nutzern in einem lokalen Netzwerk auszutauschen.
Die Kommunikation basiert auf einem eigens entwickelten Protokoll namens Simple Local Chat Protocol (SLCP).
Das Programm besteht aus mehreren gleichzeitig laufenden Prozessen, die über Interprozesskommunikation (IPC) miteinander kommunizieren.
Zur Umsetzung werden sowohl UDP als auch TCP eingesetzt – abhängig vom jeweiligen Zweck.
Die Prozesse werden mithilfe von Python-Threads und dem Multiprocessing-Modul gestartet und verwaltet.

Ablauf nach Programmstart 

Nach dem Start des Programms fragt das Hauptmenü den Nutzer zunächst nach einem Handle (Benutzernamen) ab. Optional kann dabei eine neue Konfigurationsdatei erstellt werden. Anschließend wird ein eindeutiger Konfigurationspfad basierend auf dem Handle angelegt.
Daraufhin wird ein freier TCP-Port ermittelt, der für die spätere Kommunikation mit dem Netzwerkprozess verwendet wird. Das Socket, das zur Port suche verwendet wurde, wird sofort wieder geschlossen.
Im nächsten Schritt wird ein prozesssicheres, gemeinsam genutztes Dictionary angelegt. Dieses wird initialisiert und in einer globalen Variable gespeichert. Spätere Zugriffe auf die aktuelle Nutzerliste erfolgen über eine Funktion.
Dann wird der Discovery-Dienst als separater Prozess gestartet. Dieser lauscht auf bestimmten UDP-Nachrichten wie JOIN, WHO oder LEAVE und aktualisiert entsprechend die Nutzerliste.
Nach dem Start wird der aktuelle Nutzer im System registriert. Zusätzlich wird der eigentliche Netzwerkprozess in einem weiteren Hintergrundprozess gestartet. Damit der Nutzer von Beginn an im Netzwerk sichtbar ist, wird sofort eine JOIN-Nachricht gesendet. Diese UDP-Nachricht informiert alle Discovery-Dienste über den neuen Teilnehmer (z. B. JOIN Felix 5000). Der Discovery-Dienst lauscht seinerseits über einen konfigurierten UDP-Port und speichert bei Empfang von JOIN den Handle, die IP und den TCP-Port des Nutzers in der globalen Nutzerliste.
Im Hauptprogramm läuft nun eine Menü-Schleife, über die verschiedene Funktionen gesteuert werden:

Menüoptionen

Option 1: Nutzerliste abfragen
Wird diese ausgewählt, wird ein WHO-Befehl per TCP an den eigenen Netzwerkprozess gesendet. Dieser leitet die Anfrage per UDP-Broadcast an alle Discovery-Dienste weiter. Diese antworten per Unicast mit ihren bekannten Nutzern. Der Netzwerkprozess empfängt diese Listen und sendet sie per TCP zurück an das Hauptprogramm. Es wird auf diese Antwort gewartet und danach formatiert ausgegeben, wenn sie mit knownusers beginnt.
Option 2: Textnachricht senden
Hier wird über TCP eine Nachricht mit Empfänger-Handle und Nachrichtentext an den Netzwerkprozess gesendet. Dieser verarbeitet die Nachricht, ermittelt den Empfänger und versendet die Nachricht per UDP. Der Netzwerkprozess des Empfängers empfängt diese und gibt sie aus oder reagiert gegebenenfalls mit einer Auto-Reply.
Option 3: Bild senden
Ähnlich wie bei Option 2 per TCP Befehl, Empfänger und Bildpfad an den Netzwerkprozess gesendet. Nun wird zunächst ein Header und dann die binären Bilddaten per UDP-Unicast an den Empfänger gesendet. Der Empfänger verarbeitet das: Es prüft, ob das Bild für ihn bestimmt ist, extrahiert die Bildgröße, empfängt die Daten, prüft die Byteanzahl und ermittelt den Absender. Anschließend wird das Bild im vorgesehenen Pfad aus der Konfiguration gespeichert.
Option 4: Auto-Reply aktivieren/deaktivieren
Durch diese Option, wird die Konfigurationsdatei so verändert, dass der Wert bei Autoreply aktiv von false zu true und wieder andersrum geändert wird. So muss man nicht erst den Text vom Auto-Reply leeren. 
Option 5: Auto-Reply ändern
Diese Option lädt die aktuelle Konfigurationsdatei und erlaubt dem Nutzer die Eingabe eines Auto-Reply-Textes. Im Anschluss wird der Wert von Auto-Repley aktiv auf true gesetzt und speichert die aktualisierte Konfiguration.
Option 6: Konfiguration anzeigen
Die aktuell verwendete Konfigurationsdatei wird ausgegeben.
Option 7: Programm beenden (LEAVE)
Es wird per TCP ein LEAVE-Befehl mit Handle an den Netzwerkprozess gesendet. Dieser sendet sowohl per UDP-Broadcast als auch per Unicast eine LEAVE-Nachricht an alle Discovery-Dienste. Der lokale Nutzer wird dabei aus der Liste entfernt, und die Discovery-Dienste entfernen ihn ebenfalls aus ihrer Liste und geben eine entsprechende Meldung aus. Daraufhin werden die beiden Hintergrundprozesse (Discovery und Netzwerk) beendet. 
_____________________

Weitere Informationen

 zu unseren Entscheidungen/Herausforderungen: 

Programmiersprache: Python, da es eine simplere Syntax hat und das Team die Möglichkeit gesehen hat, eine weitere Programmiersprache kennenzulernen.

Bibliotheken: 
toml: zum Einlesen und Schreiben von Konfigurationsdateien
socket: für die Netzwerkkommunikation (TCP/UDP)
os: für die Netzwerkkommunikation (TCP/UDP)
threading: zur Ausführung paralleler Empfangsprozesse
time: für Zeitstempel, Pausen und Zeitmessung
multiprocessing (Process, Manager): zur Prozessverwaltung/ gemeinsamen Nutzung von Daten

Doku: Doxygen (für Python-kompatible Kommentare)

IDE: Als IDE wird Visual Studio Code (VS Code) verwendet. Vor allem wegen der einfachen Bedienung, der übersichtlichen Benutzeroberfläche und der Git-Integration
Nachteil: Das Benötigte muss manuell installiert werden, während beispielsweise Pycharm schon alles enthält.

Programm ausführen: Programm ausführen: Für WSL wird eine Virtual Environment (venv) benötigt.
Die Version von TOML muss in dem eigenen Virtual Environment abgespeichert werden.
Zum Starten des Programms muss die venv als Quelle aktiviert werden, da die TOML-Version sonst nicht geladen wird. Eine virtuelle Umgebung ist besonders hilfreich, wenn man an mehreren Projekten gleichzeitig arbeitet, die jeweils unterschiedliche Versionen von Bibliotheken oder Programmiersprachen benötigen. So lässt sich die Kompatibilität auf dem eigenen System sicherstellen.

Betriebssystem: LINUX, da es allgemein eine einfache Basis für den Code liefert.
Nachteil: 
Das Broadcasting von virtuellen Maschinen (Windows) ist nicht möglich. Es ist eine alternative Socket-Einstellung notwendig.
Die korrekte Nutzung dieser Optionen ist plattformunabhängig. SO_REUSEPORT wird z. B. unter Windows nicht unterstützt, was die Implementierung erschwert.



Verantwortungsbereiche
Das Team hat einzelne Themenbereiche auf Personen aufgeteilt:
Discovery-Service: Mozda
Messages senden: Büsra (Bild), Tuna (Text)
Config, TOML, IPC: Nadine
UI: Jana

Zu Beginn des Projekts hat das Team die Arbeit in klar abgegrenzte Teilbereiche aufgeteilt. Jede Person übernahm ein eigenes Modul – etwa die Benutzeroberfläche, den Netzwerkprozess, den Discovery-Dienst, Nachrichtenversendung (Text und Bild) und die Netzwerkkommunikation.
Ziel war es, möglichst schnell Fortschritte zu machen, indem parallel an den verschiedenen Funktionen gearbeitet wurde. Dabei testete zunächst jeder sein Modul eigenständig und unabhängig von den anderen Komponenten.
Beim späteren Zusammenführen der Module traten jedoch mehrere Probleme auf. So kam es zum Beispiel vor, dass Nachrichten nicht korrekt beim Empfänger ankamen oder JOIN- und WHO-Anfragen nicht wie erwartet verarbeitet wurden. Auch die Autoreply-Funktion funktionierte in dieser Phase noch nicht zuverlässig. Besonders herausfordernd war die Bildübertragung: Hier wurden die Daten teilweise unvollständig empfangen oder falsch abgespeichert.
Die Bildübertragung war auch etwas herausfordernd. Es wurde versucht, Bilder komplett per UDP zu versenden. Das funktionierte bei kleinen Dateien zwar problemlos, stieß aber bei größeren Bildern schnell an technische Grenzen, da UDP keine Garantie für die Zustellung und keine automatische Aufteilung in passende Datenstücke vornimmt. Eine mögliche Alternative mit TCP wurde kurz diskutiert, aber wegen der zusätzlichen Komplexität (Peer-to-Peer-Verbindungen, zusätzlicher Steuerungsaufwand) wieder verworfen. Das Team entschied sich dafür, nur Bilder bis zu einer bestimmten Maximalgröße zuzulassen. Dadurch konnte die gesamte Übertragung weiterhin über UDP erfolgen, ohne dass aufwändige Maßnahmen zur Paketreihenfolge oder Wiederherstellung nötig wurden. Ergänzt wurde die Lösung durch einen Timeout beim Empfang, falls keine Daten ankommen oder der Empfang zu lange dauert, wird der Vorgang abgebrochen.
Ein zusätzliches Problem entstand durch die parallele Arbeit im Git-Repository: Da mehrere Teammitglieder gleichzeitig an denselben Dateien – vor allem netzwerkprozess.py und message_handler.py – arbeiteten, kam es häufig zu Konflikten beim Pushen und Pullen. In mehreren Fällen wurde Code versehentlich überschrieben, was zu Datenverlust und zusätzlichem Aufwand führte. Diese Erfahrung zeigte dem Team, dass eine bessere Koordination und Kommunikation notwendig war.
Daraufhin wurde die Zusammenarbeit angepasst: Änderungen an zentralen Dateien wurden vorher abgesprochen, und es wurde darauf geachtet, dass nicht mehr mehrere Personen gleichzeitig im selben Bereich arbeiten. Außerdem unterstützten sich die Mitglieder gegenseitig in Live-Sitzungen, in denen gemeinsam getestet und debuggt wurde. So können Probleme schneller identifiziert und gelöst werden.
Diese engere Zusammenarbeit führte zu deutlichen Verbesserungen im Projekt. Die Interprozesskommunikation zwischen UI und Netzwerkprozess wurde einheitlich per TCP umgesetzt, davor hatten wir nämlich fälschlicherweise die Befehle nicht über einen Netzwerkprozess verarbeitet, sondern wie Variablen behandelt, die einfach übergeben wurden. Wir änderten dann anschließend die Nutzung von Subprocessing zu der Nutzung von Multiprocessing, da diese bei einem reinen Python-Projekt sinnvoller waren. Außerdem wurden die Discovery-Antworten überarbeitet, damit WHO-Anfragen zuverlässig funktionierten, und die Konfiguration mit benutzerspezifischen Toml-Dateien wurde stabil integriert. Wir fanden heraus, dass unser Projekt aufgrund eines fälschlich mehrfach gestarteten Discovery-Dienstes nicht lief und auch die Autoreply-Funktion ließ sich nun über das CLI-Menü aktivieren und dauerhaft speichern. Die Bildübertragung per UDP wurde finalisiert und zuverlässig getestet.
In der letzten Phase des Projekts wurde das gesamte System mehrfach getestet – auch auf mehreren Geräten im selben Netzwerk. Zusätzlich wurde die technische Dokumentation mithilfe von Doxygen erstellt, Screenshots und Architekturdiagramme vorbereitet und eine PowerPoint-Präsentation mit Live-Demo entwickelt, um das Projekt zum Abschluss überzeugend vorzustellen.
