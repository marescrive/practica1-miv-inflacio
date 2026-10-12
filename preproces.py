import pandas as pd

# Càrrega de l'IPC-U desestacionalitzat (BLS via FRED), sèrie CPIAUCSL.
# Renombrem les columnes perquè la capçalera del CSV de FRED ha canviat amb el temps.
df = pd.read_csv("CPIAUCSL.csv")
df.columns = ["date", "cpi"]
df["date"] = pd.to_datetime(df["date"])

# --- Neteja: octubre de 2025 no té dada. Interpolació lineal entre setembre i novembre.
# Només afecta un punt; el marquem per poder-lo indicar a la visualització.
df["interpolat"] = df["cpi"].isna()
df["cpi"] = df["cpi"].interpolate(method="linear")
print(df.loc[944:946])

# --- Els 10 darrers mandats: any d'investidura -> (etiqueta, partit)
mandats = {
    1989: ("G. H. W. Bush", "Republicà"),
    1993: ("Clinton I", "Demòcrata"),
    1997: ("Clinton II", "Demòcrata"),
    2001: ("G. W. Bush I", "Republicà"),
    2005: ("G. W. Bush II", "Republicà"),
    2009: ("Obama I", "Demòcrata"),
    2013: ("Obama II", "Demòcrata"),
    2017: ("Trump I", "Republicà"),
    2021: ("Biden", "Demòcrata"),
    2025: ("Trump II", "Republicà"),
}

# --- Operacions 1 i 2: normalitzar (índex absolut -> % acumulat respecte al gener
# de la investidura) i alinear per mes de mandat (0-48) en lloc de per data natural,
# perquè tots els mandats es puguin comparar en el mateix punt.
trams = []
for any_inv, (nom, partit) in mandats.items():
    data_base = pd.Timestamp(any_inv, 1, 1)
    cpi_base = df.loc[df["date"] == data_base, "cpi"].iloc[0]
    tram = df[(df["date"] >= data_base) &
              (df["date"] <= data_base + pd.DateOffset(months=48))].copy()
    tram["mes_de_mandat"] = (tram["date"].dt.year - any_inv) * 12 + tram["date"].dt.month - 1
    tram["inflacio_acum"] = (tram["cpi"] / cpi_base - 1) * 100
    tram["mandat"] = nom
    tram["partit"] = partit
    trams.append(tram)
dm = pd.concat(trams, ignore_index=True)

# Ordre cronològic dels mandats (no alfabètic) i marca de sèrie parcial.
dm["mandat"] = pd.Categorical(dm["mandat"], categories=[v[0] for v in mandats.values()], ordered=True)
dm = dm.sort_values(["mandat", "mes_de_mandat"]).reset_index(drop=True)
dm["parcial"] = dm["mandat"].map(dm.groupby("mandat", observed=True)["mes_de_mandat"].max()) < 48

# --- Validació: mes 18 contra les xifres publicades per FactCheck.org
oficial = {"Trump II": 4.34, "Biden": 12.27, "G. H. W. Bush": 7.67,
           "G. W. Bush II": 5.90, "Clinton II": 2.38, "Clinton I": 3.92}
m18 = dm[dm["mes_de_mandat"] == 18].set_index("mandat")["inflacio_acum"]
for nom, valor in oficial.items():
    print(f"{nom:15} calculat={m18[nom]:6.2f}  FactCheck={valor:6.2f}  dif={m18[nom]-valor:+.2f}")
print(m18.round(2))

# --- Operació 3: tractament d'outliers i agrupació.
# Outlier segons el criteri de Tukey (Q3 + 1,5·IQR) sobre la inflació acumulada al mes 18,
# l'únic punt on tots els mandats són comparables. El MARQUEM però no l'eliminem:
# treure'l falsejaria la comparació; a la visualització el podrem ressaltar o filtrar.
q1, q3 = m18.quantile([0.25, 0.75])
tanca_superior = q3 + 1.5 * (q3 - q1)
outliers = m18[m18 > tanca_superior].index
dm["outlier"] = dm["mandat"].isin(outliers)
print("Tanca superior:", round(tanca_superior, 2), "| Outliers:", list(outliers))

# L'agrupació per partit ja és a la columna 'partit' (filtrable a la visualització).
print(dm.groupby("partit", observed=True)["mandat"].nunique())

# --- Verificacions i desat
print(dm.shape)
print(dm.groupby("mandat", observed=True)["mes_de_mandat"].agg(["min", "max", "count"]))
dm.to_csv("inflacio_per_mandat.csv", index=False, encoding="utf-8")