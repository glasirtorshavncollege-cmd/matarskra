# Matskrá til MagicINFO

Ein sjálvvirkandi skíggjasíða, sum heintar matskránna av Glasir-heimasíðuni og vísir hana sum fimm kassar.

## Legg á GitHub

1. Ger eina nýggja almenna GitHub-goymslu, t.d. `glasir-matskra`.
2. Legg allar fílurnar í hesi mappu í goymsluna.
3. Far í **Settings → Pages**.
4. Undir **Build and deployment** velur tú **Deploy from a branch**.
5. Vel **main**, mappuna **/(root)** og trýst **Save**.
6. Far í **Actions → Dagfør matskrá → Run workflow**, so fyrsta dagføringin verður koyrd beinanvegin.

Síðan verður vanliga:

`https://BRUKARANAVN.github.io/glasir-matskra/`

Hesa adressuna leggur tú inn sum **Web URL** í MagicINFO.

## Sjálvvirkandi dagføring

GitHub Actionin koyrir hvønn tíma og dagførir `menu.json`. HTML-síðan lesur JSON-fíluna aftur 15. hvønn minutt og endurlesur alla síðuna hálvan hvønn tíma.

## Royn lokalt

Tí `fetch()` ikki altíð riggar frá einari vanligari `file://`-adressu, kanst tú royna við:

```bash
python3 -m http.server 8000
```

Lat síðani upp `http://localhost:8000`.
