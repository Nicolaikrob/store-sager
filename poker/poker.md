# Beregning af sandsynligheder for pokerhænder

**TL;DR:** For en **eksakt** sandsynlighed i **1v1 preflop all-in** kræver en **naiv** optælling, at man i princippet gennemløber **ca. 2,1 milliarder** ($2\,097\,572\,400$) (modstander, board)-tilfælde; med **udnyttelse af symmetrier** kan det **reduceres** til færre **kanoniske** tilfælde uden at ændre svaret. **Monte Carlo-sampling** kan **estimere** det på **sekunder** i mit setup — ved en **optimeret** implementation **under ét sekund**. Monte Carlo er **enkelt og fleksibelt**; **eksakte** beregninger er **sværere at udlede og implementere**. Med Monte Carlo kan du dække **1v1**, **1v1v1** eller **flere** modstandere, **preflop** og scenarier med **kendt board** (fx efter **flop**, **turn** med fire fælleskort, eller **river** med fem).

---

I all-in-situationer skal vi kende vinder­sandsynligheden for at kunne beslutte, om vi vil gå all-in eller folde.

For at beregne den sandsynlig­hed **preflop** (ingen fælleskort endnu) kan vi bruge kombinatorik.

**Spørgsmål:** Givet mine to startkort — hvad er sandsynligheden for at vinde?

---

## Opsætning heads-up (1 mod 1)

| Symbol | Betydning |
|--------|-----------|
| **H** | Min hånd |
| **O** | Modstanderens hånd |

Vinder­sandsynligheden for min hånd **H** er et gennemsnit over alle modstander­hænder:

$$
P(\text{win} \mid H) = \sum_{O} P(O=o) \cdot P(W \mid H, O)
$$

For **faste** startkort **h** (mine) og **o** (modstanderens) — konkrete hænder — skriver vi $B_{h,o}$ og betinger på $h,o$ i stedet for det tilfældige par $(H,O)$:

- $B_{h,o}$ — mængden af alle 5-korts boards, der kan deles ud fra rest­kortene, når **h** og **o** er fjernet. Hvert board er en 5-delmængde af de 48 kort, så $|B_{h,o}| = \binom{48}{5}$.
- $\text{win}(B)$ — for det faste par $(h,o)$ er værdien $1$, hvis **h** vinder på board $B$, og $0$, hvis **h** taber (uafgjort behandles ikke endnu). Hænderne er faste; kun $B$ varierer i summen.

$$
P(W \mid h, o) = \frac{1}{|B_{h,o}|} \sum_{B \in B_{h,o}} \text{win}(B) \cdot P(B \mid h, o)
$$

---

## Størrelsesorden og udnyttelse af symmetrier

Modstanderen vælger 2 af 50 ufordelte kort; boardet vælger 5 af de resterende 48:

$$
\binom{50}{2}\binom{48}{5} = 1225 \times 1\,712\,304 = 2\,097\,572\,400
$$

Det er antallet af præcise **(modstanderhånd, board)**-par for en fast helt-hånd.

Derudover har jeg også ladet ChatGPT undersøge, hvordan man kan gøre det bedre. Jeg har ikke sat mig grundigt ind i indholdet i boksen nedenfor, **men** det giver alligevel en **idé** om, at man kan gøre det bedre.

Poker har symmetrier: et fuldt spil har 13 kortværdier og 4 kulører, og de symmetrier kan udnyttes. ChatGPT beskriver en reduktion via Burnsides lemma og ender med tallene nedenfor.

> **Ved** at bruge **kulør­symmetri** og **Burnsides lemma** (gruppeteori, der tæller forskellige tilfælde, når nogle tilstande er ækvivalente), **kan** vi erstatte de naive $2\,097\,572\,400$ **(modstander, board)**-par med en mindre mængde **kanoniske** par — stadig **eksakt**, ikke en approksimation.

Antallet af kanoniske par afhænger af håndtypen:

| Din hånd | Eksempel | Kanoniske (modstander + board)-tilfælde | vs. naiv ($\approx$) |
|----------|----------|------------------------------------------|------------------------|
| Par | A♠A♥ | $533\,775\,132$ | $\times 3{,}9$ færre |
| Suited | A♠K♠ | $356\,684\,394$ | $\times 5{,}9$ færre |
| Offsuit | A♠K♥ | $1\,055\,864\,304$ | $\times 2{,}0$ færre |

**Altså:** **med symmetri og Burnside opnår vi** det samme **eksakte** preflop-svar mod en uniformt tilfældig modstander, mens vi kun skal gennemregne tabellens midter­kolonne (hver række har en vægt, så sandsynlighederne stadig summer korrekt).

---

## Monte Carlo — simpelt, fleksibelt og tilstrækkeligt

Ovenfor er den **eksakte** tilgang — interessant, men **ikke nødvendig** i praksis. Man kan i stedet **lave Monte Carlo-sampling**: simulere mange tilfældige fordelinger af modstanderhænder og board og estimere $P(\text{win} \mid H)$.

Den kombinatoriske fremgangsmåde er **bundet til ét scenarie** (fx preflop, heads-up). Et andet setup (flere spillere, anden gade) kræver typisk **ny matematik og ny implementering**.

**Monte Carlo** er derimod **fleksibel**: samme idé virker til **flere modstandere** (3, 4, … spillere), så længe man kan definere, hvornår heltens hånd “vinder” eller deler potten.

I `mc_poker.py` ligger en lille sampler (hurtigt skrevet, **ikke** optimeret: ren Python, ingen parallelisering, ikke kompileret som C). Den er **god nok til formålet**; man kan altid optimere senere, men det er sjældent nødvendigt her. Jeg kører den på en **stinkpad** (ThinkPad) med en **svag CPU** og **ingen GPU af betydning** — det er rigeligt til scriptet; hurtigere maskine giver bare kortere ventetid ved store `N`.

---

## Equity

I poker kan en hånd ende **uafgjort** (delt pot). Tidligere i noten så vi bort fra det ved kun at tale om ren **sejr**; i Monte Carlo‑delen bruger vi **equity**.

**Equity** er din **forventede andel af potten**: har du fx **60 % equity**, betyder det, at du i gennemsnit får **60 % af potten tilbage** over mange ens situationer.

Med **Monte Carlo** estimeres equity som gennemsnit af det, du **faktisk får** hver simulation — **1** ved ren sejr, **0** ved tab, og ved uafgjort **$1/k$** af potten, hvis **$k$ spillere** deler den bedste hånd (`mc_poker.py` summerer det som **sejre + brøk‑uafgjort**). I **heads-up** er uafgjort et **to‑vejs split** ($k=2$), så hver tie‑runde bidrager med **$1/2$**.

**Bemærk:** Det er ikke sikkert, at en **spiludbyder** giver **alle pengene** tilbage ved uafgjort (spiludbyderens cut). I **1v1** antager formlen ovenfor, at **uafgjort** giver **halvdelen** af potten ($\tfrac{1}{2}$). Hvis ikke det er tilfældet at man får alle penge tilbage skal det korrigeres for.

$$
\widehat{\text{equity}} = \frac{W + \frac{1}{2}\,T}{N}\,,
$$

hvor $W$ er antal sejre, $T$ er antal **uafgjorte runder** (kun når split altid er 50/50), og $N$ er antal samples. Med **flere spillere** erstattes den faste **$\tfrac{1}{2}$** af den korrekte **$1/k$** pr. runde.

---

## Eksempelresultater

**95 % CI** i `mc_poker.py` er $\hat E \pm 1/\sqrt{N}$ for equity‑estimatet $\hat E$ (fejlmargin $\sim 1/\sqrt{N}$).

Jeg har kørt scriptet for både **heads-up** (én mod én) og med **tre spillere** (helt mod to modstandere). Tabellen nedenfor viser typiske **equity**-estimater, **95 % CI** og pladsholdere til **køretider** på **min thinkpad**.

Estimaterne er fra **preflop**: i hver simulation trækkes alle fem fælleskort tilfældigt (ingen kendt flop endnu). Selve sampleren er ikke begrænset til det — i `mc_poker.py` kan du med **`BOARD_CARDS`** låse **0–5** kort fast, fx flop (3), efter turn (4) eller hele boardet ved **river** (5).

| Situation | **Equity** (ca., erstatter $P(\text{win}\mid H)$ her) @10k samples | 95 % CI @10k samples| Køretid (thinkpad / `mc_poker.py`) |
|-----------|----------------------------------------------------------|---------|-------------------------------------|
| **A♥ K♠** · heads-up | $\approx 65{,}19\,\%$ | $64{,}2\,\%$–$66{,}2\,\%$ | 10k: 0.1 s · 100k: 1.1 s · 1M: 12 s |
| **2♥ 3♠** · heads-up | $\approx 35{,}3\,\%$ | $34{,}3\,\%$–$36{,}3\,\%$ | 10k: 0.1 s · 100k: 1.1 s · 1M: 12 s |
| **A♥ K♠** · mod to modstandere | $\approx 47{,}78\,\%$ | $46{,}8\,\%$–$48{,}8\,\%$ | 10k: 0.17 s · 100k: 1.6 s · 1M: 16.4 s |
| **2♥ 3♠** · mod to modstandere | $\approx 19{,}92\,\%$ | $18{,}9\,\%$–$20{,}9\,\%$ | 10k: 0.17 s · 100k: 1.6 s · 1M: 16.4 s |

Skru op for `N_SAMPLES` i scriptet når du vil have smallere konfidensinterval; køretid skalerer groft med $N$.

---

## Sådan bruges scriptet

Øverst i `mc_poker.py` sætter du **`HERO_CARDS`** (heltens to kort), **`NUM_OPPONENTS`** og **`N_SAMPLES`**. Kort angives som rang + kulørbogstav, som beskrevet i filens kommentar — fx `Ah`, `Ks`.

**`BOARD_CARDS`** er valgfri: du kan lægge **0–5** kendte fælleskort ind (fx et flop eller flop + turn); de resterende board-kort trækkes tilfældigt i hver simulation, så du både kan køre **preflop** (tom liste — alle fem fælleskort tilfældige hver gang) og **efter** at dele af boardet er kendt.

Output pr. kørsel: **`equity`** og **`ci_95`** med $\hat E \pm 1/\sqrt{N}$ ($\hat E$ = estimat af equity).


---
## Betting i praksis

I klassiske odds‑formler er **$p$** ofte **vindersandsynlighed** ved ét udfald. Kommer du fra **`mc_poker.py`**, har du i stedet **equity** **$E \in [0,1]$** (forventet pot‑andel, inkl. **uafgjort**). Du kan **sætte $E$ ind hvor $p$ står** — fair odds skriver du så som **$O_{\text{fair}} = 1/p$** **eller** **$O_{\text{fair}} = 1/E$**, alt efter hvilket scenariet.

Kender du **$p$** (eller **$E$** som ovenfor), kan du sammenligne med de **decimalodds**, bookmakeren udbyder, og vurdere om et spil er attraktivt.

### Fair decimalodds (uden margin)

Mellem **fair** odds og “styrke” $p$ (eller equity $E$) gælder ved ét simpelt udfald:

$$
O_{\text{fair}} = \frac{1}{p} \quad\text{eller}\quad O_{\text{fair}} = \frac{1}{E}
$$

Eksempler (samme tal med $p$ eller $E$):

| $p$ eller $E$ | Fair odds $O_{\text{fair}} = 1/p$ eller $1/E$ |
|-----------------|------------------------------------------------------|
| 50 % | $2{,}00$ |
| 33 % | $3{,}00$ |

### Margin og value

**Bettingssider** tjener typisk ved at give dig **lavere** odds end det fair tal — fx **1,95** i stedet for **2,00**, når linjen svarer til omkring 50 %.

Du har **value**, når **tilbudte odds** er **højere** end $1/p$ (eller $1/E$): fx du vurderer $p = 50\,\%$ ($O_{\text{fair}} = 2$), men kan spille til **2,05**.

### All-in poker og indsats

I **all-in poker** vil jeg antage, at vi får **en form for odds**, vi kan spille på — og med **`mc_poker.py`** kan vi estimere **equity** $E$ til at sammenligne med dem. I **1v1 preflop** vil jeg tænke, at vi får et odds **fx. 1,95**, hvis huset tager en del af **cuttet**. Jeg er selvfølgelig ikke sikker på, hvordan reglerne er for det all-in poker, vi snakker om, men vi har en **sampler** i `mc_poker.py`, der kan regne de relevante tal, og så kan **oddset** ses.

---
## Optimal stake sizing og kelly-kriteriet

Når man kender sine **odds**, **sandsynligheder** og **pengepung**, kan man benytte sig af **stake-size-teori** for at vælge, hvor mange penge man vil **satse** for at vinde over tid. Jeg kender **Kelly-kriteriet** fra tidligere beskæftigelse med betting — [se her på wiki](https://en.wikipedia.org/wiki/Kelly_criterion), hvis du er interesseret.

**Fx.** kan vi med en **pengepung** på **10.000 kr.** beregne **equity** for **A♥ K♠** heads-up ($\approx 65{,}19\,\%$), og hvis vi får **decimalodds 1,95**, kan vi med **Kelly-kriteriet** finde ud af, hvor stor en **andel af bankrollen** vi optimalt skal **satse** (her med **$E$** som **$p$** i formlen ovenfor). I praksis kan man vælge at være konservativ og kun bruge **fx. 5 % af Kelly-andelen** (*fractional Kelly*), fordi **tilfældige udsving** — selv med fornuftig indsatsstyring — stadig kan give tab.

Ved **decimalodds** $O$ og **$p$** (klassisk sejrssandsynlighed) er Kelly-andelen (andel af bankrollen pr. spil)

$$
f^* = \frac{p\,O - 1}{O - 1}\,.
$$

Med **equity** $E$ fra tabellen sætter du **$p := E$** i samme udtryk — dvs. $f^* = \dfrac{E\,O - 1}{O - 1}$ — fordi $E$ er dit **numeriske estimat** af “hvor stor en andel af potten du i gennemsnit får” i den situation.

Med $E = 0{,}6519$ (ca. $65{,}19\,\%$ **equity** for **A♥ K♠** heads-up i tabellen) og $O = 1{,}95$:

$$
f^* = \frac{0{,}6519 \cdot 1{,}95 - 1}{1{,}95 - 1} \approx 0{,}285 \quad\text{(ca.\ 28,5\,\% af bankrollen ved fuld Kelly).}
$$

Med **10.000 kr.** svarer fuld Kelly til ca. **2.850 kr.** pr. spil. Bruger man **5 % af Kelly**, bliver andelen ca. $0{,}05 \cdot 0{,}285 \approx 1{,4\,\%}$ af bankrollen — dvs. omkring **140 kr.** ved samme bankroll.