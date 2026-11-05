# Plaggverket

Personlig svensk garderobsstudio för Vinted och Plick. Körbar lokal webbapp med Flask, SQLite och filbaserad bildlagring. Inga konton hos plattformarna behövs och inga betalda tjänster är aktiverade.

## Hämta appen från GitHub

Öppna repot i GitHub, klicka på den gröna **Code**-knappen och välj **Download ZIP**. Packa upp hela ZIP-filen. Öppna den uppackade mappen och följ snabbstarten nedan. Nedladdning av koden startar eller publicerar inte appen.

Personliga annonsexempel, stilprofiler, sparade plagg, bilder, databas och hemligheter ingår inte i repot. En egen stilprofil kan importeras under **Min stil** efter att appen har startat.

## Starta på din dator

Python 3.12 eller senare rekommenderas. Snabbstart: på Windows dubbelklicka `start.bat`; på macOS/Linux kör `sh start.sh` i projektmappen. Skripten installerar kostnadsfria beroenden och startar appen. Alternativt kör kommandona nedan.

```sh
cd Reselling-automatation
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Öppna `http://127.0.0.1:5000` i din egen webbläsare. Windows: använd `python` i stället för `python3`, och `.venv\Scripts\python.exe` i stället för `.venv/bin/python`. Avsluta med Ctrl+C. Samma startkommando efter omstart behåller arbetet.

I den här molnmiljön är beroendena installerade i `/workspace/.venvs/resell`; starta från repokatalogen med `/workspace/.venvs/resell/bin/python app.py`. Molnserverns loopbackadress är inte en publik förhandsvisning eller åtkomlig på din telefon.

## Flödet för ett plagg

1. Skapa ett utkast. Ange storlek, skick, kända fakta och eventuella defekter. Lämna inköpspriset tomt om det är okänt.
2. Lägg till flera JPG/PNG/WebP-bilder (produkt, etikett, defekt). HEIC måste konverteras före uppladdning. Originalen sparas oförändrade, inklusive eventuell kamerametadata.
3. Kontrollera fakta, antingen manuellt eller från den valfria lokala AI:n. AI-förslag överförs endast med knapptryckning, måste därefter bekräftas, och obesvarade osäkerheter blockerar bekräftelse.
4. Välj bakgrund. Kantbaserad friläggning är en enkel bildalgoritm som fungerar på enfärgade bakgrunder, inte semantisk AI-segmentering. Dåligt resultat: ändra känslighet, måla en manuell mask, eller välj original. Varje vald bild måste godkännas. Etiketter/defekter behålls som original i gränssnittet. Välj ordning och omslag.
5. Spara annonsexempel och redigera stilprofilen i Min stil. Regelbaserad text använder bekräftade fakta, inledning/avslutning, radindelning och emojis. Ton, fritt ordval, stilregler och exempel tolkas av lokal AI när sådan är ansluten. Ingen modellträning. Ändringar i texterna sparas; endast uttryckligen valda stilrättningar används framåt.
6. Lägg in verkliga jämförelser (pris, datum, uppgifter, valfri länk/skärmbild). Belagt slutpris kräver källa och uttrycklig bekräftelse. Prisförslaget använder median av slutpriser när de finns, annars annonserade priser; intervallen är schabloner. Välj relevanta jämförelser av samma märke, typ, storlek och skick. Ingen automatisk justering eller webbsökning görs och säkerheten redovisas som låg. Ändra priser per plattform själv.
7. Granska och godkänn. Ladda ned ZIP med separata texter och bilder per plattform eller kopiera titel/beskrivning separat. Alla ändringar återkallar godkännandet.
8. Publicera själv i Vinted/Plick. Fyll i aktuella kategorier, märken, skick, storlek, färg, material, frakt och övriga obligatoriska fält. Kontrollera aktuella bildkrav och regler. Klistra in länken och bekräfta manuell publicering i appen.
9. Registrera försäljningen med datum, faktiskt pris och egna kostnader. Vinst = försäljningspris − inköpspris − avgifter − egen frakt − andra försäljningskostnader. Utan inköpspris är vinsten okänd. Den andra plattformens aktiva annons får en borttagningsvarning och måste tas bort och bekräftas manuellt.

Fakta och annonstext autosparas efter 0,5 s samt före navigering/åtgärder. Osynkade textändringar har också en reservkopia i den aktuella webbläsarens lokala lagring; vid återöppning av plagget får du välja att återställa dem. Bilder måste slutföra uppladdningen. Rensa webbläsardata på delade enheter. Kontrollera ”Utkast sparat”; fel sparar inte över föregående utkast. Samtidiga webbläsarändringar ger en versionskonflikt. Separata formulär för publicering, försäljning, jämförelser och stil sparas med respektive knapp.

## Valfri riktig AI, lokalt

Ingen AI-modell följer med och bildidentifiering/OCR är **inte verifierad i denna miljö**, eftersom ingen Ollama-server eller modell finns. Ingen simulerad AI-data används. Det kompletta manuella flödet fungerar ändå.

Installera Ollama från dess officiella webbplats på din egen dator. Välj en bildkapabel modell som ryms i ditt RAM/VRAM. Exempel: `gemma3:4b` (flera GB nedladdning; licens och hårdvarubehov ska kontrolleras). Detta laddas inte ned automatiskt och innebär ingen betald API-användning. Du står för datorns resurser och eventuell datatrafik.

```sh
ollama pull gemma3:4b
# Starta Ollama enligt dess installationsanvisningar, sedan appen:
OLLAMA_MODEL=gemma3:4b .venv/bin/python app.py
```

`OLLAMA_URL` är valfri (standard `http://127.0.0.1:11434`); bara loopbackservrar accepteras. Anslutningen är serversidig, har 180 s timeout och bilder lämnar appen endast till den lokala modellen när du trycker på AI-knappen. Modellen måste stödja bilder och JSON. AI-fakta och text är förslag, inte verifierade produktuppgifter. Alla påståenden ska granskas av dig.

## Verifierade begränsningar (2026-11-05)

Försök att läsa `https://www.vinted.se/terms_and_conditions` och `https://plick.se/villkor` stoppades med HTTP CONNECT 403 av miljöns nätverkspolicy. Plick-sökvägen är inte bekräftad. Det bevisar inget om plattformarnas faktiska funktioner eller regler. Inget dokumenterat, tillåtet publicerings-API har kunnat verifieras. Det finns ingen direktpublicering, automatisk borttagning, scraping, automatisk marknadsdatainsamling eller kundchatt. Inga privata API:er eller plattformslösenord används.

Bildkrav är ännu inte verifierade. Därför sker ingen plattformsspecifik beskärning, skalning eller påstådd storleksanpassning: originalets dimensioner bevaras, bakgrundsbyten exporteras som PNG. Kontrollera aktuella krav före manuell uppladdning. Exporten beskriver detta och påstår aldrig att den publicerar.

## Kostnader och säker drift

- **App:** gratis att köra lokalt. Internetdrift kan medföra hostingavgift och är inte konfigurerad.
- **Lagring:** SQLite och bilder i `data/`, ingen molnlagring eller lagringsavgift från appen. Disk och backup är ditt ansvar.
- **AI:** lokal Ollama har ingen API-avgift men använder egen hårdvara. Betald AI är inte implementerad/aktiverad. Befintliga AI-abonnemang antas inte täcka API.

Standardbindningen är enbart `127.0.0.1`. Utan lösenord avvisas fjärrklienter och främmande Host-rubriker. För egen LAN/Internetdrift måste `RESELL_PASSWORD` sättas säkert i serverns miljö och `RESELL_HOST` konfigureras; dela inte värdet i chatten. Vid Internetdrift krävs en riktig WSGI-server bakom HTTPS-proxy och `RESELL_HTTPS=1` för Secure-cookie. Flask-utvecklingsservern ska inte internetexponeras. Den här leveransen gör ingen publik driftsättning.

Sessioner är signerade, API-skrivningar kräver CSRF-token, SQL är parametriserat, bilder valideras och filnamn genereras av servern. API:er, bilder och export kräver inloggning när lösenord är aktiverat. Loggar innehåller inte plaggfakta eller nyckelvärden. Ett enda personligt konto stöds. Ingen lösenordsåterställning eller fleranvändarhantering.

Webbmanifest finns för att lägga till appen på hemskärmen där webbläsaren stöder det; appen behöver en körande server och har inget offline-läge. Mobilen behöver en säkert åtkomlig serveradress, inte datorns loopbackadress.

## Data, backup och radering

`RESELL_DATA` kan välja en annan datamapp. Säkerhetskopiera hela datamappen när servern är stoppad, eller använd ”Ladda ned alla uppgifter” som ger portabel JSON och bilder utan sessionsnyckel. CSV finns för lager och ekonomi. ZIP/CSV kan laddas ned från inställningar. Automatisk återimport av JSON är inte implementerad; full driftåterställning sker genom att återställa hela datamappen. Radering i appen raderar data i appen; tidigare exporter/backuper och externa annonser måste du radera separat.

## Tester

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
# Kräver lokal Chromium; alternativ sökväg via CHROMIUM:
.venv/bin/python tests/browser_flow.py
```

Browser-testet använder en separat tillfällig databas och startar/stänger sin egen server. Ingen testannons publiceras. Backendtester verifierar beständighet, osäkerhetskontroll, exportgodkännande, bildpixlar, faktisk vinst, borttagningsvarning, versionskonflikter, upprepade publiceringsbekräftelser, prisunderlag, säkerhet, dataradering och inloggning.

Stilprofiler kan exporteras och importeras separat som JSON under Min stil. Filen innehåller även dina annonsexempel och ska förvaras privat. Inledningen stöder `{plagg}`, `{färg}`, `{märke}` och `{från_märke}`, som fylls med det aktuella plaggets bekräftade fakta; dessa platshållare återanvänder aldrig exempelplaggens uppgifter.
