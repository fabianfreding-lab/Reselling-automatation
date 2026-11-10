# Webbdrift utan aktiverad betalning — förberedd, inte driftsatt

Målet är en personlig HTTPS-adress som kan användas på mobilen utan en dator hemma. Inga konton eller tjänster skapas av koden. Den lokala versionen fortsätter fungera som tidigare.

## Vad som har verifierats, 10 november 2026

PythonAnywheres officiella hjälpdokumentation anger att ett gratis konto har **en webbapp, en webbworker, 512 MiB disk och en månads utgångstid för webbappen**. Kontoägaren behöver förnya webbappen manuellt. Deras CPU-sekundskvot avser konsoler/schemalagd kod, inte webbappen enligt CPU-dokumentationen. Disken används för kod, paket, databas och bilder tillsammans; det är inte 512 MiB enbart för bilder. Diskkvoten stoppar nya skrivningar när den tar slut. Ta egna säkerhetskopior.

Källor (officiella dokument, lästa via leverantörens öppna GitHub-repo):
- https://help.pythonanywhere.com/pages/FreeAccountsFeatures/
- https://help.pythonanywhere.com/pages/DiskQuota/
- https://help.pythonanywhere.com/pages/WhatAreCPUSeconds/
- https://help.pythonanywhere.com/pages/Flask/

Denna miljö kunde ännu inte läsa den aktuella registrerings-/prissidan eller Googles AI-prislista direkt på grund av nätverksbegränsningar. Kontrollera att registreringen fortfarande erbjuder ett riktigt **Free/Beginner-konto utan betalning**, inte en tidsbegränsad betald provperiod. Om betalning, kort eller uppgradering krävs: stoppa och utred alternativ. **Skapa ingen betald plan.**

## AI är ett separat, ännu inte verifierat steg

Ollama på skoldatorn följer inte med till webbhotellet. Gratis webbdrift ger inte automatiskt AI-beräkningar. Koden har nu en valfri Gemini-anslutning för bildanalys/OCR och text, men den är **inte testad mot ett riktigt API-konto**, och aktuell gratis modell, tillgänglighet i Sverige, datavillkor och webbhotellets utgående åtkomst behöver verifieras. Ett gratiskonto på PythonAnywhere begränsar externa HTTPS-destinationer; Google-endpointen måste gå att nå genom deras tillåtna lista. Detta är en verklig möjlig blockerare för hela 0-kronorslösningen.

AI är avstängd i den nya webbkonfigurationen. Ingen modell laddas ned och ingen API-tjänst anropas av installationen. Regelbaserade texter och manuellt arbete fungerar utan AI; de märks inte om till AI-resultat.

För att senare aktivera Gemini krävs:
1. Ett Google AI-projekt utan aktiverad fakturering eller kopplat betalningskonto.
2. En aktuell bild-/JSON-kapabel modell som verkligen har en tillgänglig gratiskvot för det kontot och landet. Modellnamnet anges uttryckligen; koden väljer ingen modell själv.
3. Kontroll av hur Google behandlar bilder och texter på gratisnivån. Bilder och stilvägledning skickas till Google när användaren trycker på AI-knappen; detta skiljer sig från Ollama lokalt.
4. En privat serversidig API-nyckel. Lägg den aldrig i chatten, GitHub, frontendkod eller en offentlig fil.
5. Verifierad nätverksåtkomst från webbhotellet till `generativelanguage.googleapis.com`.

Ägaren bekräftar gratisprojektet genom `free_tier_confirmed`. Det är **inte en automatisk kontroll av Googles faktureringsstatus eller ett tekniskt kostnadstak**. Om projektet senare kopplas till betalning kan API-användning kosta pengar. Behåll projektet utan fakturering för 0 kr. Vid kvotfel visar appen ett fel och behåller utkastet; den gör ingen automatisk uppgradering, betald reservmodell eller upprepad retry.

## Installation — efter att gratis konto har skapats

1. Skapa ett gratis konto på https://www.pythonanywhere.com/ (EU-versionen kan användas om samma gratisvillkor erbjuds).
2. Öppna en privat Bash-konsol i kontot. Hämta appen till din hemkatalog:

```sh
git clone https://github.com/fabianfreding-lab/Reselling-automatation.git
cd Reselling-automatation
python3.12 -m venv .venv312
.venv312/bin/python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt
.venv312/bin/python configure_web.py
```

Använd Python 3.12 både i miljön och i webbappens inställningar. Om den versionen saknas på kontots systemavbildning: stoppa och kontrollera tillgängliga versioner innan beroenden eller låsningar ändras. `--no-cache-dir` minskar onödig diskanvändning på det lilla gratiskontot.

`configure_web.py` ber om ett eget lösenord i konsolen. Bara en saltad hash sparas i `data/mobile-access.json`. Befintliga plagg och bilder ändras inte. `data/web-settings.json` skapas endast om den saknas, med AI avstängd. Lägg aldrig till dessa filer i GitHub.

3. Under **Web**, skapa en webbapp med **Manual configuration** och Python 3.12. Välj ingen betald tjänst. Sätt Virtualenv till `/home/DITT_ANVÄNDARNAMN/Reselling-automatation/.venv312` och källkodsmapp till `/home/DITT_ANVÄNDARNAMN/Reselling-automatation`.
4. I kontots WSGI-fil, ersätt exempelkoden med:

```python
from pathlib import Path
import runpy

root = Path('/home/DITT_ANVÄNDARNAMN/Reselling-automatation')
application = runpy.run_path(str(root / 'deploy/pythonanywhere_wsgi.py'))['application']
```

Byt `DITT_ANVÄNDARNAMN` mot ditt faktiska kontonamn. Kör **inte** `app.py` eller Flask-utvecklingsservern i en konsol för webbdrift. Webbhotellets WSGI-server ska köra appen.

5. Klicka **Reload**. Öppna kontots **HTTPS-adress**, logga in och verifiera att ett utkast och en bild finns kvar efter en ny Reload. WSGI-starten vägrar att starta utan lösenord. Den använder Secure-/HttpOnly-cookie och samma privata `data`-mapp efter omstart.
6. Lägg inte till någon publik statisk sökväg till `data`. Bilder och exporter ska gå genom appens inloggning. `/static` får vid behov mappas till enbart projektets `static`-mapp.

## Flytta dina befintliga uppgifter

Stoppa först den lokala appservern. Behåll en säkerhetskopia av hela dess **data-mapp**. Den innehåller databas, originalbilder, redigeringar och stilprofil. För över en kopia privat till ditt eget webbhotellskonto och lägg den i projektets `data`-mapp **innan första riktiga användningen på webben**. Skicka inte mappen i chatten eller till ett offentligt repo. Kontrollera att `data/app.sqlite` och `data/images/` ligger på rätt nivå. Vid en redan använd molnversion behöver vi planera en sammanslagning; skriv inte över befintliga uppgifter blint.

Fullständig JSON/ZIP-export från appen är en separat exportfunktion; automatisk återimport av den exporten är ännu inte implementerad. En kopia av själva data-mappen är därför rätt väg för en full flytt i denna version.

## Senare AI-konfiguration

När punkterna om gratisprojekt och åtkomst ovan är verifierade, redigeras `data/web-settings.json` privat på servern:

```json
{
  "ai_provider": "gemini",
  "gemini_api_key": "ANGE_BARA_PRIVAT_I_SERVERNS_FILREDAKTOR",
  "gemini_model": "MODELL_MED_VERIFIERAD_GRATISKVOT",
  "free_tier_confirmed": true
}
```

Reload krävs efter ändringen. Använd ingen nyckel från ett fakturerat projekt. Sätt `ai_provider` till `none` för att stänga av alla AI-anrop på webbversionen. API-nyckeln och webbinställningarna ingår inte i appens normala dataexport eller AI-statussvar. Den lokala versionen använder fortfarande Ollama om `AI_PROVIDER` inte ändras där.

## Status för denna leverans

- WSGI-start, lösenordsskydd, databasbevarande vid ominläsning och spärrad AI utan konfiguration har testats lokalt.
- Gemini-formatet och kvotfel har kontraktstestats med test-fixtures, inte med verklig modellinferens.
- Ingen webbapp, API-nyckel, registrering eller betalning har skapats av agenten.
- Konto, skarp webbdrift, aktuell gratis AI-modell och utgående AI-åtkomst återstår innan hela flödet kan beskrivas som fungerande på mobilen för 0 kr.
