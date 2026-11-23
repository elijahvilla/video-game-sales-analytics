"""Generate the Tableau workbook (dashboard as code).

Writes tableau/vgsales_dashboard.twb, which points at tableau/vgsales_tableau.csv and
tableau/assets/header.png. Open it in Tableau Public Desktop, then File > Save to Tableau Public.

Usage: python tableau/build_workbook.py
"""
from html import escape
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CSV = HERE / "vgsales_tableau.csv"
HEADER = HERE / "assets" / "header.png"
OUT = HERE / "vgsales_dashboard.twb"
PREFS = Path.home() / "Documents" / "My Tableau Repository" / "Preferences.tps"  # Desktop reads custom palettes here
GOLD_PALETTE = ("<color-palette name='Lands Between Gold' type='ordered-sequential'>"
                "<color>#221D16</color><color>#3F3420</color><color>#64511F</color><color>#8E6F22</color>"
                "</color-palette>")
HYPER = HERE / "vgsales_tableau.hyper"

DS = "federated.vgsales0"
DASH = "Video Game Sales 1980-2016"
W_PX, H_PX = 1200, 1720

# "Lands Between" theme
BG, PANEL, BORDER = "#16130F", "#201C16", "#3A3226"
GOLD, CREAM, MUTED = "#D4AF37", "#E8DFC8", "#9A8F78"
REGION_COLORS = {  # Mario red, Sonic blue, Pokemon yellow, Zelda green
    "North America": "#E52521", "Europe": "#2E6FDB", "Japan": "#FFCB05", "Rest of World": "#3FA34D"}
PLATFORM_COLORS = {"PS2": GOLD, "X360": "#52B043", "PS3": "#2E6FDB", "Wii": "#E52521",
                   "DS": "#FF8C42", "PS": "#8FB3FF", "GBA": "#9B59B6", "PSP": MUTED}

SALES = "[sum:Sales (M units):qk]"
PCT = "[pcto:sum:Sales (M units):qk]"


def q(s):  # quoted member value for filters / color buckets
    return escape(f'"{s}"', quote=True)


def col(inst):
    return f"[{DS}].{inst}"


COLUMN_DEFS = {
    "Game": "<column datatype='string' name='[Game]' role='dimension' type='nominal' />",
    "Platform": "<column datatype='string' name='[Platform]' role='dimension' type='nominal' />",
    "Genre": "<column datatype='string' name='[Genre]' role='dimension' type='nominal' />",
    "Publisher": ("<column datatype='string' name='[Publisher]' role='dimension' type='nominal'><aliases>"
                  "<alias key='&quot;Sony Computer Entertainment&quot;' value='Sony' />"
                  "<alias key='&quot;Take-Two Interactive&quot;' value='Take-Two' />"
                  "<alias key='&quot;Konami Digital Entertainment&quot;' value='Konami' />"
                  "<alias key='&quot;Namco Bandai Games&quot;' value='Bandai Namco' /></aliases></column>"),
    "Year": "<column datatype='integer' name='[Year]' role='dimension' type='quantitative' />",
    "Decade": "<column datatype='string' name='[Decade]' role='dimension' type='nominal' />",
    "Region": ("<column datatype='string' name='[Region]' role='dimension' type='nominal'><aliases>"
               "<alias key='&quot;North America&quot;' value='N. America' />"
               "<alias key='&quot;Rest of World&quot;' value='Other' /></aliases></column>"),
    "Sales": "<column datatype='real' name='[Sales (M units)]' role='measure' type='quantitative' />",
}
INSTANCES = {
    "Platform": "<column-instance column='[Platform]' derivation='None' name='[none:Platform:nk]' pivot='key' type='nominal' />",
    "Genre": "<column-instance column='[Genre]' derivation='None' name='[none:Genre:nk]' pivot='key' type='nominal' />",
    "Publisher": "<column-instance column='[Publisher]' derivation='None' name='[none:Publisher:nk]' pivot='key' type='nominal' />",
    "Year": "<column-instance column='[Year]' derivation='None' name='[none:Year:qk]' pivot='key' type='quantitative' />",
    "Decade": "<column-instance column='[Decade]' derivation='None' name='[none:Decade:nk]' pivot='key' type='nominal' />",
    "Region": "<column-instance column='[Region]' derivation='None' name='[none:Region:nk]' pivot='key' type='nominal' />",
    "Sales": f"<column-instance column='[Sales (M units)]' derivation='Sum' name='{SALES}' pivot='key' type='quantitative' />",
    "Pct": (f"<column-instance column='[Sales (M units)]' derivation='Sum' name='{PCT}' pivot='key' type='quantitative'>"
            f"<table-calc ordering-field='{col('[none:Genre:nk]')}' ordering-type='Field' type='PctTotal' />"
            "</column-instance>"),
}


def deps(*names):
    out = []
    for n in names:
        base = "Sales" if n == "Pct" else n
        if COLUMN_DEFS[base] not in out:
            out.append(COLUMN_DEFS[base])
        out.append(INSTANCES[n])
    return "\n".join(out)


def member_filter(field, members):
    inner = "".join(f"<groupfilter function='member' level='{field}' member='{q(m)}' />" for m in members)
    return (f"<filter class='categorical' column='{col(field)}'>"
            f"<groupfilter function='union' user:ui-domain='database' user:ui-enumeration='inclusive' "
            f"user:ui-marker='enumerate'>{inner}</groupfilter></filter>")


def shared_filter(field, group):
    """Region / Decade filters shared by every sheet (driven by the dashboard dropdowns)."""
    return (f"<filter class='categorical' column='{col(field)}' filter-group='{group}'>"
            f"<groupfilter function='level-members' level='{field}' user:ui-enumeration='all' "
            f"user:ui-marker='enumerate' /></filter>")


def palette_rules():
    return (f"<encoding attr='color' field='{col('[none:Region:nk]')}' palette='Game Regions' type='palette' />"
            f"<encoding attr='color' field='{col('[none:Platform:nk]')}' palette='Game Platforms' type='palette' />")


def palette_xml():
    def pal(name, m):
        return (f"<color-palette name='{name}' type='regular'>"
                + "".join(f"<color>{m[k]}</color>" for k in sorted(m)) + "</color-palette>")
    return pal("Game Regions", REGION_COLORS) + pal("Game Platforms", PLATFORM_COLORS)


def sheet_style(extra=""):
    return f"""<style>
  <style-rule element='worksheet'><format attr='display-field-labels' scope='cols' value='false' /><format attr='display-field-labels' scope='rows' value='false' /><format attr='font-family' value='Tableau Book' /><format attr='color' value='{CREAM}' /><format attr='background-color' value='{PANEL}' /></style-rule>
  <style-rule element='table'><format attr='background-color' value='{PANEL}' /></style-rule>
  <style-rule element='title'><format attr='background-color' value='{PANEL}' /></style-rule>
  <style-rule element='axis'><format attr='color' value='{MUTED}' /><format attr='font-size' value='8' /></style-rule>
  <style-rule element='header'><format attr='color' value='{CREAM}' /><format attr='font-size' value='9' /></style-rule>
  <style-rule element='label'><format attr='color' value='{CREAM}' /><format attr='font-size' value='9' /></style-rule>
  <style-rule element='cell'><format attr='color' value='{CREAM}' /></style-rule>
  <style-rule element='gridline'><format attr='line-visibility' value='off' /></style-rule>
  <style-rule element='zeroline'><format attr='line-visibility' value='off' /></style-rule>
  <style-rule element='mark'>{palette_rules()}</style-rule>
  {extra}
</style>"""


def title(main, sub):
    return (f"<layout-options><title><formatted-text>"
            f"<run bold='true' fontcolor='{GOLD}' fontname='Tableau Bold' fontsize='14'>{escape(main)}</run>"
            f"<run>Æ&#10;</run>"
            f"<run fontcolor='{MUTED}' fontname='Tableau Book' fontsize='9'>{escape(sub)}</run>"
            f"</formatted-text></title></layout-options>")


def worksheet(name, main, sub, dep_names, rows, cols, mark, encodings="", filters="", sorts="",
              pane_style="", extra_style=""):
    slices = "".join(f"<column>{c}</column>" for c in
                     [col("[none:Region:nk]"), col("[none:Decade:nk]")])
    return f"""<worksheet name='{escape(name)}'>
  {title(main, sub)}
  <table>
    <view>
      <datasources><datasource caption='vgsales_tableau' name='{DS}' /></datasources>
      <datasource-dependencies datasource='{DS}'>
{deps(*dep_names, "Region", "Decade")}
      </datasource-dependencies>
      {filters}
      {shared_filter('[none:Region:nk]', 1)}
      {shared_filter('[none:Decade:nk]', 2)}
      {sorts}
      <slices>{slices}</slices>
      <aggregation value='true' />
    </view>
    {sheet_style(extra_style)}
    <panes>
      <pane selection-relaxation-option='selection-relaxation-allow'>
        <view><breakdown value='auto' /></view>
        <mark class='{mark}' />
        <encodings>{encodings}</encodings>
        <style><style-rule element='mark'>{pane_style}</style-rule></style>
      </pane>
    </panes>
    <rows>{rows}</rows>
    <cols>{cols}</cols>
  </table>
</worksheet>"""


def build_sheets(top_platforms, top_publishers):
    market = worksheet(
        "Market Over Time", "WORLD 1-1 TO 2016",
        "Tracked retail units per year (millions), stacked by region. The high score was set in 2008.",
        ["Year", "Sales"], col(SALES), col("[none:Year:qk]"), "Area",
        encodings=f"<color column='{col('[none:Region:nk]')}' />")

    heat = worksheet(
        "Regional Mix", "CHOOSE YOUR KINGDOM",
        "Share of each region's units by genre. Click a square to filter the dashboard.",
        ["Genre", "Pct", "Sales"], col("[none:Genre:nk]"), col("[none:Region:nk]"), "Square",
        encodings=f"<color column='{col(PCT)}' /><text column='{col(PCT)}' />",
        sorts=f"<sort class='computed' column='{col('[none:Genre:nk]')}' direction='DESC' using='{col(SALES)}' />",
        pane_style="<format attr='mark-labels-show' value='true' />",
        extra_style=(f"<style-rule element='cell'><format attr='text-format' field='{col(PCT)}' value='p0%' />"
                     f"</style-rule>"
                     f"<style-rule element='mark'><encoding attr='color' field='{col(PCT)}' "
                     f"palette='Lands Between Gold' type='interpolated' /></style-rule>"))

    platforms = worksheet(
        "Platform Lifecycles", "EXTRA LIVES",
        "Units per year, 8 best-selling platforms since 1994. Every console gets a launch, a peak, and a game over.",
        ["Year", "Platform", "Sales"], col(SALES), col("[none:Year:qk]"), "Line",
        encodings=f"<color column='{col('[none:Platform:nk]')}' />",
        filters=member_filter("[none:Platform:nk]", top_platforms)
        + f"<filter class='quantitative' column='{col('[none:Year:qk]')}' included-values='in-range'>"
          "<min>1994</min></filter>")

    pubs = worksheet(
        "Top Publishers", "FINAL BOSSES",
        "Top 10 publishers by lifetime units (millions).",
        ["Publisher", "Sales"], col("[none:Publisher:nk]"), col(SALES), "Bar",
        filters=member_filter("[none:Publisher:nk]", top_publishers),
        sorts=f"<sort class='computed' column='{col('[none:Publisher:nk]')}' direction='DESC' using='{col(SALES)}' />",
        encodings=f"<text column='{col(SALES)}' />",
        pane_style=f"<format attr='mark-color' value='{GOLD}' /><format attr='mark-labels-show' value='true' />",
        extra_style=f"<style-rule element='cell'><format attr='text-format' field='{col(SALES)}' value='n#,##0' /></style-rule>")
    return [market, heat, platforms, pubs]


def run(text, color=CREAM, size=10, bold=False, font="Tableau Book"):
    b = " bold='true'" if bold else ""
    return f"<run{b} fontcolor='{color}' fontname='{font}' fontsize='{size}'>{escape(text)}</run>"


NL = "<run>Æ&#10;</run>"


def kpi(label, value, note):
    return (run(label, GOLD, 9, True, "Tableau Bold") + NL + run(value, CREAM, 22, True, "Tableau Bold")
            + NL + run(note, MUTED, 9))


INSIGHTS = [
    ("Japan ahead, therefore role-playing.", "RPGs take 3.6x the share of units in Japan that they do in North America."),
    ("Strong foe ahead: Nintendo.", "#1 publisher in North America (19%), Europe (17%), and Japan (36%)."),
    ("Praise the PS2.", "1.23 billion units, the best-selling platform in the data. Its peak year was 2004."),
]


def insights_text():
    parts = [run("INSIGHT AHEAD", GOLD, 14, True, "Tableau Bold"), NL,
             run("Messages left for the next player", MUTED, 9), NL, NL]
    for i, (msg, fact) in enumerate(INSIGHTS):
        parts += [run(msg, GOLD, 10, True, "Tableau Bold"), NL, run(fact, CREAM, 9)]
        if i < len(INSIGHTS) - 1:
            parts += [NL, NL]
    return "".join(parts)


FOOTER = (run("DATA ", GOLD, 8, True, "Tableau Bold")
          + run("VGChartz via Kaggle (CC0), 16,187 titles, 1980-2016. Physical retail units only, so digital sales "
                "and recent years are undercounted.", MUTED, 8)
          + NL + run("BUILT BY ", GOLD, 8, True, "Tableau Bold")
          + run("Elijah Villa  |  github.com/elijahvilla/video-game-sales-analytics", MUTED, 8))


class Zones:
    """Tiled layout helper. Coordinates are in Tableau's 0-100000 units."""

    def __init__(self):
        self.next_id = 10

    def nid(self):
        self.next_id += 1
        return self.next_id

    @staticmethod
    def box(xp, yp, wp, hp):
        return (f"x='{round(xp * 100000 / W_PX)}' y='{round(yp * 100000 / H_PX)}' "
                f"w='{round(wp * 100000 / W_PX)}' h='{round(hp * 100000 / H_PX)}'")

    @staticmethod
    def card(bg=PANEL, border=True, margin=6, padding=8):
        b = (f"<format attr='border-color' value='{BORDER}' /><format attr='border-style' value='solid' />"
             f"<format attr='border-width' value='1' />") if border else ""
        return (f"<zone-style><format attr='background-color' value='{bg}' />{b}"
                f"<format attr='margin' value='{margin}' /><format attr='padding' value='{padding}' /></zone-style>")

    def sheet(self, name, xp, yp, wp, hp):
        return f"<zone id='{self.nid()}' name='{escape(name)}' {self.box(xp, yp, wp, hp)}>{self.card()}</zone>"

    def text(self, body, xp, yp, wp, hp, bg=PANEL, border=True):
        return (f"<zone id='{self.nid()}' type-v2='text' {self.box(xp, yp, wp, hp)}>"
                f"<formatted-text>{body}</formatted-text>{self.card(bg, border)}</zone>")

    def image(self, path, xp, yp, wp, hp):
        return (f"<zone id='{self.nid()}' is-scaled='1' param='{escape(path.as_posix())}' type-v2='bitmap' "
                f"{self.box(xp, yp, wp, hp)}>{self.card(BG, False, 0, 0)}</zone>")

    def filt(self, field, xp, yp, wp, hp):
        return (f"<zone id='{self.nid()}' mode='checkdropdown' name='Market Over Time' "
                f"param='{col(field)}' type-v2='filter' values='database' {self.box(xp, yp, wp, hp)}>"
                f"{self.card(margin=4, padding=2)}</zone>")

    def legend(self, sheet, field, xp, yp, wp, hp):
        return (f"<zone id='{self.nid()}' name='{escape(sheet)}' pane-specification-id='0' "
                f"param='{col(field)}' type-v2='color' {self.box(xp, yp, wp, hp)}>{self.card()}</zone>")

    def flow(self, direction, children, xp, yp, wp, hp):
        return (f"<zone id='{self.nid()}' param='{direction}' type-v2='layout-flow' {self.box(xp, yp, wp, hp)}>"
                f"{''.join(children)}</zone>")


def build_dashboard():
    """Every zone floats at an exact pixel position (tiled layouts were being resized by Tableau)."""
    z = Zones()
    zs = [z.image(HEADER, 0, 0, W_PX, 200)]

    y, hud_h = 210, 160
    kpis = [("WORLD RECORD", "82.7M", "Wii Sports, best-selling title"),
            ("FINAL BOSS PLATFORM", "1.23B", "PS2 lifetime units"),
            ("HOME-FIELD ADVANTAGE", "35.5%", "Nintendo's share of Japan")]
    zs += [z.text(kpi(*k), 20 + i * 290, y, 280, hud_h) for i, k in enumerate(kpis)]
    zs += [z.filt("[none:Region:nk]", 890, y, 290, 78),
           z.filt("[none:Decade:nk]", 890, y + 82, 290, 78)]

    y = 380
    zs += [z.sheet("Market Over Time", 20, y, 990, 370),
           z.legend("Market Over Time", "[none:Region:nk]", 1020, y, 160, 370)]

    y = 760
    zs += [z.sheet("Regional Mix", 20, y, 540, 430),
           z.sheet("Platform Lifecycles", 570, y, 470, 430),
           z.legend("Platform Lifecycles", "[none:Platform:nk]", 1050, y, 130, 430)]

    y = 1200
    zs += [z.sheet("Top Publishers", 20, y, 620, 420),
           z.text(insights_text(), 650, y, 530, 420)]

    zs.append(z.text(FOOTER, 20, 1630, 1160, 85, BG, False))

    root = f"<zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{''.join(zs)}</zone>"
    action = (f"<actions><action caption='Click a genre to filter' name='[Action1_genre]'>"
              f"<activation auto-clear='true' type='on-select' />"
              f"<source dashboard='{escape(DASH)}' type='sheet' worksheet='Regional Mix' />"
              f"<command command='tsc:tsl-filter'><param name='special-fields' value='all' />"
              f"<param name='target' value='{escape(DASH)}' /></command></action></actions>")
    dash = f"""<dashboards>
<dashboard name='{escape(DASH)}'>
  <style><style-rule element='table'><format attr='background-color' value='{BG}' /></style-rule></style>
  <size maxheight='{H_PX}' maxwidth='{W_PX}' minheight='{H_PX}' minwidth='{W_PX}' />
  <zones>{root}</zones>
</dashboard>
</dashboards>"""
    return dash, action


def datasource():
    cols = "\n".join(
        f"<column datatype='{t}' name='{n}' ordinal='{i}' />" for i, (n, t) in enumerate(
            [("Game", "string"), ("Platform", "string"), ("Genre", "string"), ("Publisher", "string"),
             ("Year", "integer"), ("Decade", "string"), ("Region", "string"), ("Sales (M units)", "real")]))
    buckets = lambda field, m: "".join(
        f"<map to='{c}'><bucket>{q(k)}</bucket></map>" for k, c in m.items())
    return f"""<datasources>
<datasource caption='vgsales_tableau' inline='true' name='{DS}' version='18.1'>
  <connection class='federated'>
    <named-connections>
      <named-connection caption='vgsales_tableau' name='textscan.vgsales0'>
        <connection class='textscan' directory='{escape(CSV.parent.as_posix())}' filename='{CSV.name}' password='' server='' />
      </named-connection>
    </named-connections>
    <relation connection='textscan.vgsales0' name='vgsales_tableau.csv' table='[vgsales_tableau#csv]' type='table'>
      <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
{cols}
      </columns>
    </relation>
  </connection>
{chr(10).join(COLUMN_DEFS.values())}
  <extract count='-1' enabled='true' units='records'>
    <connection access_mode='readonly' author-locale='en_US' authentication='auth-none' class='hyper' dbname='{escape(HYPER.as_posix())}' default-settings='yes' schema='Extract' sslmode='' tablename='Extract' username='tableau_internal_user'>
      <relation name='Extract' table='[Extract].[Extract]' type='table' />
    </connection>
  </extract>
  <style>
    <style-rule element='mark'>
      <encoding attr='color' field='[none:Region:nk]' type='palette'>{buckets('Region', REGION_COLORS)}</encoding>
      <encoding attr='color' field='[none:Platform:nk]' type='palette'>{buckets('Platform', PLATFORM_COLORS)}</encoding>
    </style-rule>
  </style>
</datasource>
</datasources>"""


def main():
    df = pd.read_csv(CSV)
    s = "Sales (M units)"
    top_platforms = df.groupby("Platform")[s].sum().nlargest(8).index.tolist()
    top_publishers = df.groupby("Publisher")[s].sum().nlargest(10).index.tolist()
    assert top_platforms == list(PLATFORM_COLORS), top_platforms

    dash, action = build_dashboard()
    sheet_cards = ("<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' />"
                   "<card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'>"
                   "<card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>"
                   "<strip size='31'><card type='title' /></strip></edge></cards>")
    windows = "".join(f"<window class='worksheet' name='{escape(n)}'>{sheet_cards}</window>" for n in
                      ["Market Over Time", "Regional Mix", "Platform Lifecycles", "Top Publishers"])
    viewpoints = "".join(f"<viewpoint name='{escape(n)}'><zoom type='entire-view' /></viewpoint>" for n in
                         ["Market Over Time", "Regional Mix", "Platform Lifecycles", "Top Publishers"])
    windows += (f"<window class='dashboard' maximized='true' name='{escape(DASH)}'>"
                f"<viewpoints>{viewpoints}</viewpoints><active id='-1' /><device-preview /></window>")
    xml = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build='2025.1.0 (20251.25.0101.0000)' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
<document-format-change-manifest />
<preferences>
  {GOLD_PALETTE}
  {palette_xml()}
</preferences>
<style />
{datasource()}
{action}
<worksheets>
{chr(10).join(build_sheets(top_platforms, top_publishers))}
</worksheets>
{dash}
<windows>{windows}</windows>
</workbook>
"""
    OUT.write_text(xml, encoding="utf-8")
    PREFS.write_text("<?xml version='1.0'?>\n<workbook>\n<preferences>\n" + GOLD_PALETTE + palette_xml()
                     + "\n</preferences>\n</workbook>\n", encoding="utf-8")
    print("wrote", PREFS)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
